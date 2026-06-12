import pandas as pd

df = pd.read_csv(
    "cleaned/property_listing_history.csv",
    encoding="latin1",
    low_memory=False
)

# Keep only records with a development
df = df[df["NormalizedDevelopment"].notna()]
df = df[df["NormalizedDevelopment"] != ""]

summary = (
    df.groupby("NormalizedDevelopment")
    .agg(
        ListingCount=("List Number", "count"),
        UniqueProperties=("PropertyFingerprint", "nunique"),
        ActiveListings=("Status", lambda x: (x == "A").sum()),
        PendingListings=("Status", lambda x: (x == "P").sum()),
        ClosedListings=("Status", lambda x: (x == "C").sum()),
        OtherStatusListings=("Status", lambda x: (~x.isin(["A", "P", "C"])).sum()),
        AvgListPrice=("List Price USD$", "mean"),
        AvgSoldPrice=("Sold Price USD$", "mean"),
        AvgDaysOnMarket=("Days on Market", "mean"),
        AvgBedrooms=("Total Bedrooms", "mean"),
        AvgBaths=("Total Baths", "mean"),
        AvgCondoM2=("Condo M2", "mean"),
    )
    .reset_index()
)

summary = summary.sort_values(
    "UniqueProperties",
    ascending=False
)

summary.to_csv(
    "cleaned/development_analysis.csv",
    index=False
)

print("Development analysis complete.")
print("Developments:", len(summary))
print("Output written to: cleaned/development_analysis.csv")

print("\nTop 25 developments by unique properties:")
print(
    summary[
        [
            "NormalizedDevelopment",
            "UniqueProperties",
            "ListingCount",
            "ActiveListings",
            "PendingListings",
            "ClosedListings",
            "AvgListPrice",
            "AvgSoldPrice",
        ]
    ].head(25)
)