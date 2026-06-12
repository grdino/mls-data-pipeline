"""
Build historical closed-sales dataset and duplicate-review report.

Input:
- prod/data/raw/ClosedInceptionTo2026-06-05.csv

Output:
- prod/data/cleaned/historical_closed_sales.csv
- prod/data/cleaned/historical_closed_sales_duplicates_review.csv
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

HISTORICAL_INPUT_PATH = "prod/data/raw/ClosedInceptionTo2026-06-05.csv"
HISTORICAL_OUTPUT_PATH = "prod/datacleaned/historical_closed_sales.csv"
DUPLICATE_REVIEW_PATH = "prod/data/cleaned/historical_closed_sales_duplicates_review.csv"


# --------------------------------------------------
# Load historical closed-sales export
# --------------------------------------------------

df = pd.read_csv(
    HISTORICAL_INPUT_PATH,
    encoding="latin1",
    low_memory=False,
)


# --------------------------------------------------
# Apply normalization rules
# --------------------------------------------------

df = apply_property_normalization(
    df,
    use_property_name_fallback=True,
    include_building=True,
)


# --------------------------------------------------
# Add historical closed-sales reporting fields
# --------------------------------------------------

df["SoldDateParsed"] = pd.to_datetime(
    df["Sold Date"],
    errors="coerce",
)

df["SaleYear"] = df["SoldDateParsed"].dt.year
df["SaleMonth"] = df["SoldDateParsed"].dt.month

df["SaleYearMonth"] = (
    df["SoldDateParsed"]
    .dt.to_period("M")
    .astype(str)
)

df["SoldPricePerM2"] = (
    df["Sold Price USD$"] / df["Condo M2"]
)

df.loc[
    df["Condo M2"] <= 0,
    "SoldPricePerM2",
] = pd.NA


# --------------------------------------------------
# Export historical closed-sales dataset
# --------------------------------------------------

os.makedirs("cleaned", exist_ok=True)

df.to_csv(
    HISTORICAL_OUTPUT_PATH,
    index=False,
)


# --------------------------------------------------
# Create duplicate-review report for closed sales
# --------------------------------------------------

duplicate_fingerprints, duplicates_review = build_duplicate_review(df)

duplicates_review.to_csv(
    DUPLICATE_REVIEW_PATH,
    index=False,
)


# --------------------------------------------------
# Summary output
# --------------------------------------------------

print("Historical closed sales build complete.")
print("Rows:", len(df))
print("Unique fingerprints:", df["PropertyFingerprint"].nunique())
print("Output written to:", HISTORICAL_OUTPUT_PATH)
print("Duplicate review written to:", DUPLICATE_REVIEW_PATH)

print("\nTop duplicate fingerprints:")
print(duplicate_fingerprints[duplicate_fingerprints > 1].head(25))
