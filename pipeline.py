import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
df = pd.read_csv("data/raw/insurance.csv")

print("Shape: ", df.shape)
print("\nFirst five rows")
print(df.head())
print("\nColumn types")
print(df.dtypes)
print("\nMissing values per column")
print(df.isna().sum())

numeric_cols = ["age", "bmi", "children", "charges"]
text_cols = ["sex", "smoker", "region"]

df_imputed = df.copy()

for col in numeric_cols:
    df_imputed[col] = df_imputed[col].fillna(df_imputed[col].mean())

for col in text_cols:
    df_imputed[col] = df_imputed[col].fillna(df_imputed[col].mode().iloc[0])

print("\nAfter imputation")
print(df_imputed.head())
print(df_imputed.dtypes)
print("Shape:", df_imputed.shape)
print("Missing values:\n", df_imputed.isna().sum())
print("Unchanged from input:", df_imputed.equals(df))

df_encoded = df_imputed.copy()

df_encoded["sex"] = df_encoded["sex"].map({"female": 0, "male": 1})
df_encoded["smoker"] = df_encoded["smoker"].map({"no": 0, "yes": 1})
df_encoded = pd.get_dummies(df_encoded, columns=["region"], dtype="int64")

print("\nAfter encoding")
print(df_encoded.head())
print(df_encoded.dtypes)
print("Shape:", df_encoded.shape)
print("Missing values:", df_encoded.isna().sum().sum())
print("Columns:", df_encoded.columns.tolist())


df_scaled = df_encoded.copy()
scale_cols = ["age", "bmi", "children"]

for col in scale_cols:
    mean = df_scaled[col].mean()
    std = df_scaled[col].std(ddof=1)
    df_scaled[col] = (df_scaled[col] - mean) / std

print("\nAfter scaling")
print(df_scaled[scale_cols + ["charges"]].head())
print("Shape:", df_scaled.shape)
print("Means:\n", df_scaled[scale_cols].mean())
print("Sample standard deviations:\n", df_scaled[scale_cols].std(ddof=1))
print("Charges unchanged:", df_scaled["charges"].equals(df_encoded["charges"]))


feature_cols = [
    "age", "bmi", "children", "sex", "smoker",
    "region_northeast", "region_northwest",
    "region_southeast", "region_southwest",
]

X = df_scaled[feature_cols].to_numpy(dtype="float64")
y = df_scaled["charges"].to_numpy(dtype="float64")

print("\nNumPy arrays")
print("Feature order:", feature_cols)
print("X shape:", X.shape, "dtype:", X.dtype)
print("y shape:", y.shape, "dtype:", y.dtype)
print("First X row:", X[0])
print("First y value:", y[0])

batch_size = 64
x_batches = []
y_batches = []

for start in range(0, len(X), batch_size):
    end = start + batch_size
    x_batches.append(X[start:end])
    y_batches.append(y[start:end])

x_sum = sum(batch.sum() for batch in x_batches)
y_sum = sum(batch.sum() for batch in y_batches)

print("\nMini-batches and checksums")
print("Number of batches:", len(x_batches))
print("First batch:", x_batches[0].shape, y_batches[0].shape)
print("Last batch:", x_batches[-1].shape, y_batches[-1].shape)
print(f"X sum: {x_sum:.10f}")
print(f"y sum: {y_sum:.10f}")


X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

model = RandomForestRegressor(random_state=42)
model.fit(X_train, y_train)

print("\nRandom Forest")
print("Train:", X_train.shape, y_train.shape)
print("Test:", X_test.shape, y_test.shape)
print("Test R²:", model.score(X_test, y_test))