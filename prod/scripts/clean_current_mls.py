"""
Clean the current MLS export and create a duplicate-review report.

Input:
- prod/data/raw/textexport.csv
- optional prod/data/raw/listing_geo_lookup.csv

Output:
- prod/data/cleaned/textexport_cleaned.csv
- prod/data/cleaned/fingerprint_duplicates_review.csv
"""

import os
import pandas as pd

from mls_normalization import (
    apply_property_normalization,
    build_duplicate_review,
)


# --------------------------------------------------
# File paths
# --------------------------------------------------

MLS_INPUT_PATH = "prod/data/raw/textexport.csv"
GEO_INPUT_PATH = "prod/data/raw/listing_geo_lookup.csv"
CLEANED_OUTPUT_PATH = "prod/data/cleaned/textexport_cleaned.csv"
DUPLICATE_REVIEW_PATH = "prod/data/cleaned/fingerprint_duplicates_review.csv"


# --------------------------------------------------
# Load raw MLS export
# --------------------------------------------------

df = pd.read_csv(
    MLS_INPUT_PATH,
    encoding="latin1",
    low_memory=False,
)


# --------------------------------------------------
# Optional: merge geo lookup file
# --------------------------------------------------

if os.path.exists(GEO_INPUT_PATH):
    geo_df = pd.read_csv(
        GEO_INPUT_PATH,
        encoding="latin1",
        low_memory=False,
    )

    geo_columns = [
        "List Number",
        "Geo Latitude",
        "Geo Longitude",
    ]

    missing_geo_columns = [
        col for col in geo_columns
        if col not in geo_df.columns
    ]

    if missing_geo_columns:
        print(
            "Geo file found, but these columns are missing:",
            missing_geo_columns,
        )
        print("Skipping geo merge.")
    else:
        geo_df = geo_df[geo_columns].drop_duplicates(
            subset=["List Number"]
        )

        df = df.merge(
            geo_df,
            on="List Number",
            how="left",
        )
else:
    print("Geo lookup file not found. Continuing without geo merge.")


# --------------------------------------------------
# Apply normalization rules
# --------------------------------------------------

df = apply_property_normalization(
    df,
    use_property_name_fallback=True,
    include_building=True,
)


# --------------------------------------------------
# Export cleaned dataset
# --------------------------------------------------

os.makedirs("cleaned", exist_ok=True)

df.to_csv(
    CLEANED_OUTPUT_PATH,
    index=False,
)


# --------------------------------------------------
# Create duplicate-review report
# --------------------------------------------------

duplicate_fingerprints, duplicates_review = build_duplicate_review(df)

duplicates_review.to_csv(
    DUPLICATE_REVIEW_PATH,
    index=False,
)


# --------------------------------------------------
# Summary output
# --------------------------------------------------

print("MLS cleaning complete.")
print("Rows:", len(df))
print("Unique fingerprints:", df["PropertyFingerprint"].nunique())
print("Cleaned file written to:", CLEANED_OUTPUT_PATH)
print("Duplicate review written to:", DUPLICATE_REVIEW_PATH)

if "Geo Latitude" in df.columns:
    print("Listings missing geo coordinates:", df["Geo Latitude"].isna().sum())

print(
    "Average listings per property:",
    round(
        len(df) / df["PropertyFingerprint"].nunique(),
        2,
    ),
)

print("\nTop duplicate fingerprints:")
print(duplicate_fingerprints[duplicate_fingerprints > 1].head(25))
