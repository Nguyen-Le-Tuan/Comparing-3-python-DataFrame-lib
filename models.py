"""Shared model workloads; dataframe backends only prepare identical arrays."""

from __future__ import annotations

import hashlib
import os
import random

import numpy as np


def array_hash(array: np.ndarray) -> str:
    """Hash integer indices in a platform-independent byte order."""
    return hashlib.sha256(np.asarray(array, dtype="<i8").tobytes()).hexdigest()


def _metrics(y_true: np.ndarray, y_pred: np.ndarray) -> None:
    from sklearn.metrics import mean_squared_error, r2_score

    if not np.all(np.isfinite(y_pred)):
        raise ValueError("Model produced non-finite predictions")
    print(f"Test R²: {r2_score(y_true, y_pred):.10f}")
    print(f"Test RMSE: {np.sqrt(mean_squared_error(y_true, y_pred)):.10f}")


def train_insurance(model_name: str, X: np.ndarray, y: np.ndarray) -> None:
    """Use the same 80/20 row split for every Insurance regressor."""
    from sklearn.model_selection import train_test_split

    train_idx, test_idx = train_test_split(
        np.arange(len(y)), test_size=0.2, random_state=42
    )
    print("Train rows:", len(train_idx))
    print("Test rows:", len(test_idx))
    print("Train index SHA-256:", array_hash(train_idx))
    print("Test index SHA-256:", array_hash(test_idx))
    X_train, X_test = X[train_idx], X[test_idx]
    y_train, y_test = y[train_idx], y[test_idx]

    if model_name == "rf":
        from sklearn.ensemble import RandomForestRegressor

        model = RandomForestRegressor(random_state=42)
        model.fit(X_train, y_train)
        predictions = model.predict(X_test)
    elif model_name == "svr":
        from sklearn.compose import TransformedTargetRegressor
        from sklearn.preprocessing import StandardScaler
        from sklearn.svm import SVR

        model = TransformedTargetRegressor(
            regressor=SVR(kernel="rbf", C=1.0, epsilon=0.1, gamma="scale"),
            transformer=StandardScaler(),
        )
        model.fit(X_train, y_train)
        predictions = model.predict(X_test)
    elif model_name == "xgboost":
        from xgboost import XGBRegressor

        model = XGBRegressor(
            objective="reg:squarederror", booster="gbtree", n_estimators=100,
            max_depth=6, learning_rate=0.1, subsample=1.0,
            colsample_bytree=1.0, tree_method="hist", device="cpu",
            n_jobs=1, random_state=42,
        )
        model.fit(X_train, y_train)
        if model.get_booster().save_config().find('"device":"cpu"') < 0:
            raise RuntimeError("XGBoost did not use the requested CPU device")
        print("Model device: cpu")
        predictions = model.predict(X_test)
    elif model_name == "tabnet":
        import torch
        from pytorch_tabnet.tab_model import TabNetRegressor
        from sklearn.preprocessing import StandardScaler

        _seed_torch(torch)
        if not torch.cuda.is_available():
            raise RuntimeError("TabNet requires cuda:0; CPU fallback is disabled")
        scaler = StandardScaler().fit(y_train.reshape(-1, 1))
        target = scaler.transform(y_train.reshape(-1, 1)).astype(np.float32)
        model = TabNetRegressor(
            n_d=8, n_a=8, n_steps=3, gamma=1.3,
            mask_type="sparsemax", lambda_sparse=0.001, seed=42,
            device_name="cuda", optimizer_fn=torch.optim.Adam,
            optimizer_params={"lr": 0.02}, verbose=0,
        )
        model.fit(
            X_train.astype(np.float32), target,
            max_epochs=20, batch_size=256, virtual_batch_size=64,
            patience=0, num_workers=0, drop_last=False,
            compute_importance=False,
        )
        if model.device.type != "cuda" or model.device.index not in (None, 0):
            raise RuntimeError(f"TabNet used unexpected device: {model.device}")
        print("Model device:", model.device)
        scaled_predictions = model.predict(X_test.astype(np.float32))
        torch.cuda.synchronize()
        predictions = scaler.inverse_transform(scaled_predictions).ravel()
    else:
        raise ValueError(f"Invalid Insurance model: {model_name}")

    _metrics(y_test, predictions)


def _seed_torch(torch: object) -> None:
    """Fail on nondeterministic kernels instead of changing the experiment."""
    if os.environ.get("CUBLAS_WORKSPACE_CONFIG") != ":4096:2":
        raise RuntimeError("Set CUBLAS_WORKSPACE_CONFIG=:4096:2 before importing PyTorch")
    random.seed(42)
    np.random.seed(42)
    torch.manual_seed(42)
    torch.backends.cudnn.benchmark = False
    torch.backends.cudnn.deterministic = True
    torch.use_deterministic_algorithms(True)


def ncf_pairs(X: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Split observed interactions by user and sample one fixed zero per positive."""
    split_rng = np.random.default_rng(42)
    negative_rng = np.random.default_rng(43)
    train_positive, test_positive, train_negative, test_negative = [], [], [], []
    for user in range(X.shape[0]):
        positive_movies = np.flatnonzero(X[user] > 0)
        zero_movies = np.flatnonzero(X[user] == 0)
        if len(positive_movies) < 2 or len(zero_movies) == 0:
            raise ValueError(f"User {user} lacks positive or negative candidates")
        shuffled = split_rng.permutation(positive_movies)
        test_count = int(0.2 * len(shuffled))
        test_movies, train_movies = shuffled[:test_count], shuffled[test_count:]
        train_positive.append(np.column_stack((np.full(len(train_movies), user), train_movies)))
        test_positive.append(np.column_stack((np.full(len(test_movies), user), test_movies)))
        train_negative.append(np.column_stack((
            np.full(len(train_movies), user),
            negative_rng.choice(zero_movies, size=len(train_movies)),
        )))
        test_negative.append(np.column_stack((
            np.full(len(test_movies), user),
            negative_rng.choice(zero_movies, size=len(test_movies)),
        )))
    return tuple(np.concatenate(parts).astype(np.int64) for parts in (
        train_positive, test_positive, train_negative, test_negative
    ))


def train_movielens(model_name: str, X: np.ndarray) -> None:
    if model_name == "svd":
        from sklearn.decomposition import TruncatedSVD

        factors = TruncatedSVD(n_components=50, random_state=42).fit_transform(X)
        print("SVD output shape:", factors.shape)
        return
    if model_name != "ncf":
        raise ValueError(f"Invalid MovieLens model: {model_name}")

    import torch
    from sklearn.metrics import roc_auc_score
    from torch import nn
    from torch.utils.data import DataLoader, TensorDataset

    _seed_torch(torch)
    if not torch.cuda.is_available():
        raise RuntimeError("NCF requires cuda:0; CPU fallback is disabled")
    train_pos, test_pos, train_neg, test_neg = ncf_pairs(X)
    if len(train_pos) + len(test_pos) != 1_000_209:
        raise ValueError("NCF positive interactions do not match MovieLens-1M")
    for label, pairs in zip(
        ("train positive", "test positive", "train negative", "test negative"),
        (train_pos, test_pos, train_neg, test_neg), strict=True,
    ):
        print(f"{label} pairs: {len(pairs)} SHA-256: {array_hash(pairs)}")
    train_pairs = np.concatenate((train_pos, train_neg))
    test_pairs = np.concatenate((test_pos, test_neg))
    train_labels = np.concatenate((np.ones(len(train_pos)), np.zeros(len(train_neg)))).astype(np.float32)
    test_labels = np.concatenate((np.ones(len(test_pos)), np.zeros(len(test_neg)))).astype(np.float32)

    class NCF(nn.Module):
        def __init__(self) -> None:
            super().__init__()
            self.users = nn.Embedding(X.shape[0], 32)
            self.movies = nn.Embedding(X.shape[1], 32)
            self.mlp = nn.Sequential(
                nn.Linear(64, 64), nn.ReLU(), nn.Linear(64, 32), nn.ReLU(),
                nn.Linear(32, 16), nn.ReLU(), nn.Linear(16, 1),
            )

        def forward(self, users, movies):
            return self.mlp(torch.cat((self.users(users), self.movies(movies)), dim=1)).squeeze(1)

    device = torch.device("cuda:0")
    model = NCF().to(device)
    print("Model device:", next(model.parameters()).device)
    optimizer = torch.optim.Adam(model.parameters(), lr=0.001, weight_decay=0)
    criterion = nn.BCEWithLogitsLoss(reduction="mean")
    dataset = TensorDataset(torch.from_numpy(train_pairs), torch.from_numpy(train_labels))
    loader = DataLoader(
        dataset, batch_size=4096, shuffle=True, drop_last=False,
        num_workers=0, generator=torch.Generator().manual_seed(42),
    )
    model.train()
    for _ in range(5):
        for pairs, labels in loader:
            pairs, labels = pairs.to(device), labels.to(device)
            optimizer.zero_grad(set_to_none=True)
            loss = criterion(model(pairs[:, 0], pairs[:, 1]), labels)
            loss.backward()
            optimizer.step()
    model.eval()
    logits = []
    with torch.no_grad():
        for start in range(0, len(test_pairs), 4096):
            pairs = torch.from_numpy(test_pairs[start:start + 4096]).to(device)
            logits.append(model(pairs[:, 0], pairs[:, 1]).cpu())
    scores = torch.cat(logits)
    loss = criterion(scores, torch.from_numpy(test_labels)).item()
    auc = roc_auc_score(test_labels, scores.numpy())
    torch.cuda.synchronize()
    if not np.isfinite(loss) or not np.isfinite(auc):
        raise ValueError("NCF produced non-finite test metrics")
    print(f"Test BCE: {loss:.10f}")
    print(f"Test ROC AUC: {auc:.10f}")
