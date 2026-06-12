import pandas as pd

# --------------------------------------------------
# Load listing history
# --------------------------------------------------

df = pd.read_csv(
    "cleaned/property_listing_history.csv",
    encoding="latin1",
    low_memory=False
)

# --------------------------------------------------
# Active listings only
# --------------------------------------------------

active = df[df["Status"] == "A"].copy()

# --------------------------------------------------
# Calculate price per square meter
# Mainly useful for condos
# --------------------------------------------------

active["PricePerM2"] = (
    active["List Price USD$"] /
    active["Condo M2"]
)

active.loc[
    active["Condo M2"] <= 0,
    "PricePerM2"
] = pd.NA

active["MarketSegment"] = (
    active["Pre-Construction"]
    .fillna("No")
)

# Change so that median price displays as currency instead of scientific notation
pd.set_option("display.float_format", "{:,.2f}".format)

# --------------------------------------------------
# Community-level market statistics
# --------------------------------------------------

community_stats = (
    active.groupby(["Community", "MarketSegment"])
    .agg(
        ActiveListings=("List Number", "count"),
        UniqueProperties=("PropertyFingerprint", "nunique"),

        MedianListPrice=("List Price USD$", "median"),
        MeanListPrice=("List Price USD$", "mean"),

        MedianPricePerM2=("PricePerM2", "median"),
        MeanPricePerM2=("PricePerM2", "mean"),

        MedianBedrooms=("Total Bedrooms", "median"),
        MeanBedrooms=("Total Bedrooms", "mean"),

        MedianBaths=("Total Baths", "median"),
        MeanBaths=("Total Baths", "mean"),

        MedianCondoM2=("Condo M2", "median"),
        MeanCondoM2=("Condo M2", "mean"),

        MedianDOM=("Days on Market", "median"),
        MeanDOM=("Days on Market", "mean")
    )
    .reset_index()
)

community_stats = community_stats.sort_values(
    "ActiveListings",
    ascending=False
)

community_stats.to_csv(
    "analysis/community_market_stats.csv",
    index=False
)

# --------------------------------------------------
# Community + bedroom statistics
# --------------------------------------------------

community_bedroom_stats = (
    active.groupby(["Community", "MarketSegment", "Total Bedrooms"])
    .agg(
        ActiveListings=("List Number", "count"),
        UniqueProperties=("PropertyFingerprint", "nunique"),

        MedianListPrice=("List Price USD$", "median"),
        MeanListPrice=("List Price USD$", "mean"),

        MedianPricePerM2=("PricePerM2", "median"),
        MeanPricePerM2=("PricePerM2", "mean"),

        MedianCondoM2=("Condo M2", "median"),
        MeanCondoM2=("Condo M2", "mean"),

        MedianDOM=("Days on Market", "median"),
        MeanDOM=("Days on Market", "mean")
    )
    .reset_index()
)

community_bedroom_stats = community_bedroom_stats.sort_values(
    ["Community", "Total Bedrooms"]
)

community_bedroom_stats.to_csv(
    "analysis/community_bedroom_stats.csv",
    index=False
)

# --------------------------------------------------
# Summary output
# --------------------------------------------------

print("Community analysis complete.")
print("Active listing rows:", len(active))
print("Communities:", len(community_stats))
print("Output written to: analysis/community_market_stats.csv")
print("Output written to: analysis/community_bedroom_stats.csv")

print("\nTop 25 communities by active listings:")
print(
    community_stats[
        [
            "Community",
            "MarketSegment",
            "ActiveListings",
            "UniqueProperties",
            "MedianListPrice",
            "MeanListPrice",
            "MedianPricePerM2",
            "MedianDOM"
        ]
    ].head(25)
)