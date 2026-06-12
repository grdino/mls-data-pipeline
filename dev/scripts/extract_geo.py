import pandas as pd
from pathlib import Path

geo_raw_path = Path("raw/textexport_geo.csv")
geo_lookup_path = Path("cleaned/listing_geo_lookup.csv")

geo_df = pd.read_csv(
    geo_raw_path,
    encoding="latin1",
    low_memory=False
)

geo_lookup = geo_df[
    [
        "List Number",
        "Geo Latitude",
        "Geo Longitude",
    ]
].copy()

geo_lookup = geo_lookup.drop_duplicates(subset=["List Number"])

geo_lookup.to_csv(
    geo_lookup_path,
    index=False
)

print("Geo lookup created.")
print("Rows:", len(geo_lookup))
print("Output:", geo_lookup_path)