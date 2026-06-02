import pandas as pd

df = pd.read_csv("raw/textexport.csv")

print(f"Rows: {len(df)}")
print(f"Columns: {len(df.columns)}")

print(df.columns.tolist())
