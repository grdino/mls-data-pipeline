import pandas as pd

df = pd.read_csv(
    "cleaned/textexport_cleaned.csv",
    encoding="latin1",
    low_memory=False
)

geo_df = pd.read_csv(
    "cleaned/listing_geo_lookup.csv",
    encoding="latin1",
    low_memory=False
)

geo_df = geo_df[
    [
        "List Number",
        "Geo Latitude",
        "Geo Longitude",
    ]
].drop_duplicates(subset=["List Number"])

df = df.merge(
    geo_df,
    on="List Number",
    how="left"
)

# One row per unique property fingerprint
property_master = (
    df.sort_values("mod_timestamp")
    .drop_duplicates(subset=["PropertyFingerprint"], keep="last")
    [
        [
            "PropertyFingerprint",
            "Card Format",
            "NormalizedDevelopment",
            "NormalizedUnit",
            "NormalizedTaxID",
            "NormalizedAddress",
            "Community",
            "Area",
            "Zone",
            "Geo Latitude",
            "Geo Longitude",
        ]
    ]
)

# Every listing, linked to the property fingerprint
property_listing_history = df[
    [
        "List Number",
        "PropertyFingerprint",
        "Status",
        "Begin Date",
        "End Date",
        "Sold Date",
        "Status Change Date",
        "Original Price USD$",
        "List Price USD$",
        "Sold Price USD$",
        "Days on Market",
        "Card Format",
        "Total Bedrooms",
        "Total Baths",
        "Condo M2",
        "Lot M2",
        "NormalizedDevelopment",
        "NormalizedUnit",
        "NormalizedAddress",
        "NormalizedTaxID",
        "Zone",
        "Area",
        "Community",
        "Pre-Construction",
    ]
]

property_master.to_csv(
    "cleaned/property_master.csv",
    index=False
)

property_listing_history.to_csv(
    "cleaned/property_listing_history.csv",
    index=False
)

print("Property master build complete.")
print("MLS records:", len(df))
print("Unique properties:", len(property_master))
print("Listing history rows:", len(property_listing_history))
print("Properties with latitude:", property_master["Geo Latitude"].notna().sum())
print("Properties with longitude:", property_master["Geo Longitude"].notna().sum())