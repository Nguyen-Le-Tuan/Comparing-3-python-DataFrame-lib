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




def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--lib", choices=["pandas", "polars", "dask"], required=True)
    parser.add_argument("--data", choices=["insurance"], required=True)
    parser.add_argument("--stage", choices=["data", "full"], required=True)
    args = parser.parse_args()

    pipelines = {
        "pandas": pandas_insurance,
        "polars": polars_insurance,
       
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
