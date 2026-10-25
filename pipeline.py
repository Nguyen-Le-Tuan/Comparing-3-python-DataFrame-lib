"""Insurance data pipeline shared by Pandas, Polars, and Dask runs."""

import argparse


DATA_PATH = "data/raw/insurance.csv"
NUMERIC_COLUMNS = ["age", "bmi", "children", "charges"]
TEXT_COLUMNS = ["sex", "smoker", "region"]
SCALE_COLUMNS = ["age", "bmi", "children"]
REGIONS = ["northeast", "northwest", "southeast", "southwest"]
FEATURE_COLUMNS = [
    "age", "bmi", "children", "sex", "smoker",
    "region_northeast", "region_northwest",
    "region_southeast", "region_southwest",
]


def pandas_insurance():
    import pandas as pd

    df = pd.read_csv(DATA_PATH)

    # Fill numeric gaps with a column mean and text gaps with the most common value.
    df_imputed = df.copy()
    for col in NUMERIC_COLUMNS:
        df_imputed[col] = df_imputed[col].fillna(df_imputed[col].mean())
    for col in TEXT_COLUMNS:
        df_imputed[col] = df_imputed[col].fillna(df_imputed[col].mode().iloc[0])

    df_encoded = df_imputed.copy()
    df_encoded["sex"] = df_encoded["sex"].map({"female": 0, "male": 1})
    df_encoded["smoker"] = df_encoded["smoker"].map({"no": 0, "yes": 1})
    df_encoded = pd.get_dummies(df_encoded, columns=["region"], dtype="int64")

    # Scale only the three inputs specified in the protocol, using sample std.
    df_scaled = df_encoded.copy()
    for col in SCALE_COLUMNS:
        mean = df_scaled[col].mean()
        std = df_scaled[col].std(ddof=1)
        df_scaled[col] = (df_scaled[col] - mean) / std

    X = df_scaled[FEATURE_COLUMNS].to_numpy(dtype="float64")
    y = df_scaled["charges"].to_numpy(dtype="float64")
    return X, y


def polars_insurance():
    import polars as pl

    lazy = pl.scan_csv(DATA_PATH)

    # Keep imputation, encoding, and scaling lazy until one final collect.
    lazy = lazy.with_columns(
        [pl.col(col).fill_null(pl.col(col).mean()) for col in NUMERIC_COLUMNS]
        + [pl.col(col).fill_null(pl.col(col).mode().first()) for col in TEXT_COLUMNS]
    )
    lazy = lazy.with_columns(
        pl.col("sex").replace_strict({"female": 0, "male": 1}).alias("sex"),
        pl.col("smoker").replace_strict({"no": 0, "yes": 1}).alias("smoker"),
        *[
            (pl.col("region") == region).cast(pl.Int64).alias(f"region_{region}")
            for region in REGIONS
        ],
    ).drop("region")
    lazy = lazy.with_columns(
        [
            ((pl.col(col) - pl.col(col).mean()) / pl.col(col).std(ddof=1)).alias(col)
            for col in SCALE_COLUMNS
        ]
    ).select(FEATURE_COLUMNS + ["charges"])

    df_scaled = lazy.collect()
    X = df_scaled.select(FEATURE_COLUMNS).to_numpy().astype("float64", copy=False)
    y = df_scaled["charges"].to_numpy().astype("float64", copy=False)
    return X, y


def dask_insurance():
    import dask.dataframe as dd

    ddf = dd.read_csv(DATA_PATH)
    print("Dask partitions:", ddf.npartitions)

    # Build the dataframe graph with default read block size and scheduler.
    for col in NUMERIC_COLUMNS:
        ddf[col] = ddf[col].fillna(ddf[col].mean())
    for col in TEXT_COLUMNS:
        mode = ddf[col].mode().compute().iloc[0]
        ddf[col] = ddf[col].fillna(mode)

    ddf["sex"] = ddf["sex"].map({"female": 0, "male": 1}, meta=("sex", "int64"))
    ddf["smoker"] = ddf["smoker"].map({"no": 0, "yes": 1}, meta=("smoker", "int64"))
    ddf = ddf.categorize(columns=["region"])
    ddf = dd.get_dummies(ddf, columns=["region"], dtype="int64")

    # After mode/category discovery, keep scaling lazy until the final compute.
    for col in SCALE_COLUMNS:
        ddf[col] = (ddf[col] - ddf[col].mean()) / ddf[col].std(ddof=1)
    df_scaled = ddf[FEATURE_COLUMNS + ["charges"]].compute()
    X = df_scaled[FEATURE_COLUMNS].to_numpy(dtype="float64")
    y = df_scaled["charges"].to_numpy(dtype="float64")
    return X, y


def pandas_movielens():
    import pandas as pd

    base = "data/raw/ml-1m"
    ratings = pd.read_csv(
        f"{base}/ratings.dat",
        sep="::", engine="python", header=None, encoding="latin-1",
        names=["UserID", "MovieID", "Rating", "Timestamp"],
    )
    users = pd.read_csv(
        f"{base}/users.dat",
        sep="::", engine="python", header=None, encoding="latin-1",
        names=["UserID", "Gender", "Age", "Occupation", "Zip-code"],
        dtype={"Zip-code": "string"},
    )
    movies = pd.read_csv(
        f"{base}/movies.dat",
        sep="::", engine="python", header=None, encoding="latin-1",
        names=["MovieID", "Title", "Genres"],
    )

    print("Input shapes:", ratings.shape, users.shape, movies.shape)

    if ratings.duplicated(["UserID", "MovieID"]).any():
        raise ValueError("Duplicate user–movie rating; do not aggregate silently")

    joined = (
        ratings
        .merge(users, on="UserID", how="inner", validate="many_to_one")
        .merge(movies, on="MovieID", how="inner", validate="many_to_one")
    )
    if len(joined) != len(ratings):
        raise ValueError("A join dropped ratings")
    print("Joined shape:", joined.shape)

    matrix_df = joined.pivot(
        index="UserID", columns="MovieID", values="Rating"
    )
    matrix_df = matrix_df.sort_index().sort_index(axis=1).fillna(0.0)

    X = matrix_df.to_numpy(dtype="float64")
    user_ids = matrix_df.index.to_numpy(dtype="int64")
    movie_ids = matrix_df.columns.to_numpy(dtype="int64")

    if X.shape != (6040, 3706):
        raise ValueError(f"Unexpected ML-1M matrix shape: {X.shape}")

    return X, user_ids, movie_ids


def polars_movielens():
    import numpy as np
    import polars as pl

    base = "data/raw/ml-1m"

    def scan_dat(filename, column_names, encoding="utf8"):
        # Unit separator không xuất hiện trong ba file ML-1M hiện tại.
        # Do đó mỗi dòng được scan thành một cột "raw".
        return (
            pl.scan_csv(
                f"{base}/{filename}",
                has_header=False,
                separator="\x1f",
                quote_char=None,
                new_columns=["raw"],
                encoding=encoding,
            )
            .select(
                pl.col("raw")
                .str.split_exact("::", len(column_names) - 1)
                .struct.rename_fields(column_names)
                .alias("fields")
            )
            .unnest("fields")
        )

    ratings = scan_dat(
        "ratings.dat", ["UserID", "MovieID", "Rating", "Timestamp"]
    ).with_columns(
        pl.col("UserID").cast(pl.Int64),
        pl.col("MovieID").cast(pl.Int64),
        pl.col("Rating").cast(pl.Int64),
        pl.col("Timestamp").cast(pl.Int64),
    )

    users = scan_dat(
        "users.dat",
        ["UserID", "Gender", "Age", "Occupation", "Zip-code"],
    ).with_columns(
        pl.col("UserID").cast(pl.Int64),
        pl.col("Age").cast(pl.Int64),
        pl.col("Occupation").cast(pl.Int64),
    )

    movies = scan_dat(
        "movies.dat",
        ["MovieID", "Title", "Genres"],
        encoding="utf8-lossy",
    ).with_columns(
        pl.col("MovieID").cast(pl.Int64),
    )

    joined_lazy = (
        ratings
        .join(users, on="UserID", how="inner", validate="m:1")
        .join(movies, on="MovieID", how="inner", validate="m:1")
    )

    # Một lần collect: scan, parse và hai join được thực thi ở đây.
    joined = joined_lazy.collect()
    if joined.height != 1_000_209:
        raise ValueError(f"A join dropped ratings: {joined.height}")
    print("Joined shape:", joined.shape)

    if joined.select(
        pl.struct("UserID", "MovieID").is_duplicated().any()
    ).item():
        raise ValueError("Duplicate user–movie rating; do not aggregate silently")

    # Pivot eager: số MovieID được đánh giá chỉ biết sau khi đọc dữ liệu.
    wide = joined.pivot(
        on="MovieID",
        index="UserID",
        values="Rating",
        aggregate_function=None,
    )

    # Tên cột pivot là chuỗi; sort trực tiếp có thể cho 1, 10, 100, 2.
    # Vì vậy phải đổi sang int để sắp xếp theo MovieID thật.
    movie_ids = sorted(int(col) for col in wide.columns if col != "UserID")
    movie_columns = [str(movie_id) for movie_id in movie_ids]
    wide = wide.sort("UserID").select(["UserID"] + movie_columns)

    user_ids = wide["UserID"].to_numpy().astype("int64", copy=False)
    X = (
        wide.select(movie_columns)
        .fill_null(0.0)
        .to_numpy()
        .astype("float64", copy=False)
    )
    movie_ids = np.asarray(movie_ids, dtype="int64")

    if X.shape != (6040, 3706):
        raise ValueError(f"Unexpected ML-1M matrix shape: {X.shape}")

    return X, user_ids, movie_ids




def run_movielens(stage):
    import hashlib
    import numpy as np

    X, user_ids, movie_ids = pandas_movielens()
    batch_size = 64
    batches = [
        X[start:start + batch_size]
        for start in range(0, len(X), batch_size)
    ]
    x_sum = sum(batch.sum(dtype=np.float64) for batch in batches)

    user_hash = hashlib.sha256(
        np.asarray(user_ids, dtype="<i8").tobytes()
    ).hexdigest()
    movie_hash = hashlib.sha256(
        np.asarray(movie_ids, dtype="<i8").tobytes()
    ).hexdigest()

    print("X shape:", X.shape, "dtype:", X.dtype)
    print("Number of batches:", len(batches))
    print("Nonzero ratings:", np.count_nonzero(X))
    print(f"X sum: {x_sum:.10f}")
    print("UserID order SHA-256:", user_hash)
    print("MovieID order SHA-256:", movie_hash)

    if stage == "full":
        from sklearn.decomposition import TruncatedSVD

        model = TruncatedSVD(n_components=50, random_state=42)
        user_factors = model.fit_transform(X)
        print("SVD output shape:", user_factors.shape)



def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--lib", choices=["pandas", "polars", "dask"], required=True)
    parser.add_argument("--data", choices=["insurance","ml-1m"], required=True)
    parser.add_argument("--stage", choices=["data", "full"], required=True)
    args = parser.parse_args()

    if args.data == "ml-1m":
        if args.lib != "pandas":
            parser.error("ML-1M currently supports pandas only")
        run_movielens(args.stage)
        return


    pipelines = {
        "pandas": pandas_insurance,
        "polars": polars_insurance,
        "dask": dask_insurance,
    }
    X, y = pipelines[args.lib]()

    # Sum the actual file-order mini-batches, not an unused full array.
    batch_size = 64
    x_batches = []
    y_batches = []
    for start in range(0, len(X), batch_size):
        end = start + batch_size
        x_batches.append(X[start:end])
        y_batches.append(y[start:end])
    x_sum = sum(batch.sum() for batch in x_batches)
    y_sum = sum(batch.sum() for batch in y_batches)

    print("Feature order:", FEATURE_COLUMNS)
    print("X shape:", X.shape, "dtype:", X.dtype)
    print("y shape:", y.shape, "dtype:", y.dtype)
    print(f"X sum: {x_sum:.10f}")
    print(f"y sum: {y_sum:.10f}")

    if args.stage == "full":
        from sklearn.ensemble import RandomForestRegressor
        from sklearn.model_selection import train_test_split

        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )
        model = RandomForestRegressor(random_state=42)
        model.fit(X_train, y_train)
        print("Test R²:", model.score(X_test, y_test))


if __name__ == "__main__":
    main()
