import pandas as pd

property_master = pd.read_csv(
    "cleaned/property_master.csv",
    encoding="latin1",
    low_memory=False
)

listing_history = pd.read_csv(
    "cleaned/property_listing_history.csv",
    encoding="latin1",
    low_memory=False
)

print("PROPERTY ANALYSIS")
print("-----------------")

print("\nProperty master rows:", len(property_master))
print("Listing history rows:", len(listing_history))

print("\nProperties by Card Format:")
print(property_master["Card Format"].value_counts())

print("\nListings by Status:")
print(listing_history["Status"].value_counts())

print("\nTop 25 Developments by Property Count:")
print(
    property_master["NormalizedDevelopment"]
    .value_counts()
    .head(25)
)

print("\nTop 25 Properties by Number of Listings:")
print(
    listing_history["PropertyFingerprint"]
    .value_counts()
    .head(25)
)

print("\nAverage Listings Per Property:")
print(
    round(
        len(listing_history) / len(property_master),
        2
    )
)

print("\nProperties missing development:")
print(
    property_master[
        property_master["NormalizedDevelopment"] == ""
    ].shape[0]
)

print("\nProperties missing tax id:")
print(
    property_master[
        property_master["NormalizedTaxID"] == ""
    ].shape[0]
)