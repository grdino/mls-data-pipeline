import pandas as pd

df = pd.read_csv(
    "cleaned/textexport_cleaned.csv",
    encoding="latin1",
    low_memory=False
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