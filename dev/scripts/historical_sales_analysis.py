import pandas as pd

df = pd.read_csv(
    "cleaned/historical_closed_sales.csv",
    encoding="latin1",
    low_memory=False
)

# Closed condo sales only, for first version
sales = df[
    (df["Status"] == "C") &
    (df["Card Format"] == "Condos")
].copy()

# Remove invalid DOM values
sales.loc[
    sales["Days on Market"] < 0,
    "Days on Market"
] = pd.NA

sales = sales[
    sales["SoldDateParsed"].notna()
]

community_monthly = (
    sales.groupby(["Community", "SaleYearMonth"])
    .agg(
        SalesCount=("List Number", "count"),
        UniqueProperties=("PropertyFingerprint", "nunique"),
        MedianSoldPrice=("Sold Price USD$", "median"),
        MeanSoldPrice=("Sold Price USD$", "mean"),
        MedianSoldPricePerM2=("SoldPricePerM2", "median"),
        MeanSoldPricePerM2=("SoldPricePerM2", "mean"),
        MedianDOM=("Days on Market", "median"),
        MeanDOM=("Days on Market", "mean"),
        MedianBedrooms=("Total Bedrooms", "median"),
        MedianBaths=("Total Baths", "median"),
        MedianCondoM2=("Condo M2", "median"),
    )
    .reset_index()
)

community_monthly.to_csv(
    "analysis/community_monthly_sales_stats.csv",
    index=False
)

community_bedroom_sales = (
    sales.groupby(["Community", "Total Bedrooms"])
    .agg(
        SalesCount=("List Number", "count"),
        UniqueProperties=("PropertyFingerprint", "nunique"),
        MedianSoldPrice=("Sold Price USD$", "median"),
        MeanSoldPrice=("Sold Price USD$", "mean"),
        MedianSoldPricePerM2=("SoldPricePerM2", "median"),
        MeanSoldPricePerM2=("SoldPricePerM2", "mean"),
        MedianDOM=("Days on Market", "median"),
        MeanDOM=("Days on Market", "mean"),
        MedianCondoM2=("Condo M2", "median"),
    )
    .reset_index()
)

community_bedroom_sales.to_csv(
    "analysis/community_bedroom_sales_stats.csv",
    index=False
)

# --------------------------------------------------
# Community / Bedroom / Month (2026 only)
# --------------------------------------------------

sales_2026 = sales[
    sales["SaleYear"] == 2026
]

community_bedroom_monthly = (
    sales_2026
    .groupby(
        [
            "Community",
            "Total Bedrooms",
            "SaleYearMonth"
        ]
    )
    .agg(
        SalesCount=("List Number", "count"),
        UniqueProperties=("PropertyFingerprint", "nunique"),
        MedianSoldPrice=("Sold Price USD$", "median"),
        MeanSoldPrice=("Sold Price USD$", "mean"),
        MedianSoldPricePerM2=("SoldPricePerM2", "median"),
        MedianDOM=("Days on Market", "median")
    )
    .reset_index()
)

community_bedroom_monthly.to_csv(
    "analysis/community_bedroom_monthly_2026.csv",
    index=False
)

print(
    "Output written to: analysis/community_bedroom_monthly_2026.csv"
)

print("Historical sales analysis complete.")
print("Closed condo sales:", len(sales))
print("Output written to: analysis/community_monthly_sales_stats.csv")
print("Output written to: analysis/community_bedroom_sales_stats.csv")

print("\nTop community/month rows:")
print(community_monthly.head(25))