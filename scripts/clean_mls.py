import pandas as pd
import re

df = pd.read_csv(
    "raw/textexport.csv",
    encoding="latin1",
    low_memory=False
)

def normalize_unit(value):
    if pd.isna(value):
        return ""

    value = str(value).upper().strip()

    value = re.sub(r"\b(SUITE|UNIT|APT|APARTMENT|DEPTO|DEPARTAMENTO)\b", "", value)

    value = value.replace("|", "")
    value = value.replace("#", "")

    value = " ".join(value.split())

    value = value.replace("PH ", "PH")
    value = value.replace("P H ", "PH")
    value = re.sub(r"^(\d+)\s+PH$", r"\1PH", value)

    value = re.sub(r"^([A-Z])[\s\-]+(\d+)$", r"\1\2", value)
    value = re.sub(r"^(\d+)[\s\-]+([A-Z])$", r"\1\2", value)

    return value.strip()

def normalize_tax_id(value):
    if pd.isna(value):
        return ""

    value = str(value).upper().strip()
    value = value.replace("-", "")
    value = value.replace(" ", "")

    return value

def normalize_text(value):
    if pd.isna(value):
        return ""

    value = str(value).upper().strip()
    value = value.replace(".", "")
    value = value.replace(",", "")
    value = value.replace("&", " AND ")
    value = value.replace("Á", "A")
    value = value.replace("É", "E")
    value = value.replace("Í", "I")
    value = value.replace("Ó", "O")
    value = value.replace("Ú", "U")
    value = value.replace("Ñ", "N")
    value = " ".join(value.split())

    if value == "OTHER":
        return ""

    return value

def build_normalized_address(row):
    street_number = normalize_text(row["Street Number"])
    street_name = normalize_text(row["Street Name"])
    street_suffix = normalize_text(row["Street Suffix"])

    address = " ".join(
        part for part in [street_number, street_name, street_suffix]
        if part
    )

    return address

def build_property_fingerprint(row):

    if row["Card Format"] == "Condos":

        if (
            row["NormalizedDevelopment"]
            and row["NormalizedUnit"]
        ):
            return (
                row["NormalizedDevelopment"]
                + "|"
                + row["NormalizedUnit"]
            )

    if row["NormalizedTaxID"]:
        return row["NormalizedTaxID"]

    return row["NormalizedAddress"]

df["NormalizedUnit"] = df["Unit #"].apply(normalize_unit)
df["NormalizedTaxID"] = df["Tax ID Number"].apply(normalize_tax_id)
df["NormalizedDevelopment"] = (
    df["Development Name"]
    .apply(normalize_text)
)
df["NormalizedAddress"] = df.apply(build_normalized_address, axis=1)
df["PropertyFingerprint"] = (
    df.apply(build_property_fingerprint, axis=1)
)

# Save cleaned file
df.to_csv(
    "cleaned/textexport_cleaned.csv",
    index=False
)

# Create duplicate fingerprint review file
duplicate_fingerprints = df["PropertyFingerprint"].value_counts()

duplicates_review = (
    df[df["PropertyFingerprint"].duplicated(keep=False)]
    .sort_values("PropertyFingerprint")
)

duplicates_review.to_csv(
    "cleaned/fingerprint_duplicates_review.csv",
    index=False
)

# Summary output
print("MLS cleaning complete.")
print("Rows:", len(df))
print("Unique fingerprints:", df["PropertyFingerprint"].nunique())
print("Cleaned file written to: cleaned/textexport_cleaned.csv")
print("Duplicate review written to: cleaned/fingerprint_duplicates_review.csv")

print("\nTop duplicate fingerprints:")
print(duplicate_fingerprints[duplicate_fingerprints > 1].head(25))