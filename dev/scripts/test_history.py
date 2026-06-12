import pandas as pd

df = pd.read_csv(
    "raw/ClosedInceptionTo2026-06-5.csv",
    encoding="latin1",
    low_memory=False
)

print(df.columns.tolist())
print(len(df))
print(df.head(3))