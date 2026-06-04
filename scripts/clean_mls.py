import pandas as pd
import re

# --------------------------------------------------
# Load raw MLS export
# --------------------------------------------------

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

    # normalize house labels
    value = re.sub(r"^(CASA|HOUSE|VILLA)\s+(\d+)$", r"\2", value)

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

    # normalize common street abbreviations
    street_name = re.sub(r"^AV\s+", "AVENIDA ", street_name)
    street_name = re.sub(r"^AVE\s+", "AVENIDA ", street_name)
    street_name = re.sub(r"^BLVD\s+", "BOULEVARD ", street_name)
    street_name = re.sub(r"^BVLD\s+", "BOULEVARD ", street_name)

    # remove CALLE prefixes
    street_name = re.sub(r"^CALLE\s+", "", street_name)
    street_name = re.sub(r"^C\.\s+", "", street_name)
    street_name = re.sub(r"^C\s+", "", street_name)

    address = " ".join(
        part for part in [street_number, street_name, street_suffix]
        if part
    )

    return address

def build_normalized_development(row):
    development = normalize_text(row["Development Name"])

    if development:
        return development

    ncn = normalize_text(row["NO_COMMON_NAME"])
    unit = row["NormalizedUnit"]

    if ncn and unit:
        ncn = ncn.replace(unit, "")
        ncn = " ".join(ncn.split())

    return ncn

# ==================================================
# MLS DATA EXCEPTIONS
# Rules discovered through duplicate analysis
# ==================================================

def derive_unit_from_ncn(ncn):

    if not ncn:
        return ""

    matches = re.findall(r"\d+", ncn)

    if len(matches) == 1:
        return matches[0]

    return ""

def derive_unit_from_directions(directions):
    """
    MLS exception:

    Some condo projects store Unit # as "1" for all units.
    The actual condo number appears in Directions:

        "unit 201 floor 2"
        "unit 102 floor 1"
        "condo 304"

    Extract the first valid unit number.
    """

    if pd.isna(directions):
        return ""

    text = normalize_text(directions)

    patterns = [
        r"\bUNIT\s+([A-Z]?\d+[A-Z]?)\b",
        r"\bCONDO\s+([A-Z]?\d+[A-Z]?)\b"
    ]

    for pattern in patterns:
        match = re.search(pattern, text)

        if match:
            return match.group(1)

    return ""

def fill_missing_or_non_numeric_unit(row):

    unit = row["NormalizedUnit"]

    # --------------------------------------------------
    # Normal case:
    # Unit already contains a number
    # --------------------------------------------------

    if re.search(r"\d", unit):

        # MLS exception:
        # Some condo projects store Unit # as "1"
        # for every unit. Check Directions for a
        # more specific condo number.
        if unit == "1":

            derived = derive_unit_from_directions(
                row["Directions"]
            )

            if derived:
                return derived

        return unit

    # --------------------------------------------------
    # MLS exception:
    # Unit stored in NO_COMMON_NAME
    # --------------------------------------------------

    derived = derive_unit_from_ncn(
        normalize_text(row["NO_COMMON_NAME"])
    )

    if derived:
        return derived

    return unit

# Create the primary matching key used for duplicate detection.
# Priority:
# 1. Development + Unit
# 2. Tax ID
# 3. Address
def build_property_fingerprint(row):

    if row["NormalizedDevelopment"] and row["NormalizedUnit"]:
        return (
            row["NormalizedDevelopment"]
            + "|"
            + row["NormalizedUnit"]
        )

    if row["NormalizedTaxID"]:
        return row["NormalizedTaxID"]

    return row["NormalizedAddress"]

# --------------------------------------------------
# Apply normalization rules
# --------------------------------------------------
df["NormalizedUnit"] = df["Unit #"].apply(normalize_unit)

df["NormalizedUnit"] = (
    df.apply(fill_missing_or_non_numeric_unit, axis=1)
)
df["NormalizedTaxID"] = df["Tax ID Number"].apply(normalize_tax_id)
df["NormalizedDevelopment"] = (
    df.apply(build_normalized_development, axis=1)
)
df["NormalizedAddress"] = df.apply(build_normalized_address, axis=1)
df["PropertyFingerprint"] = (
    df.apply(build_property_fingerprint, axis=1)
)

# --------------------------------------------------
# Export cleaned dataset
# --------------------------------------------------
df.to_csv(
    "cleaned/textexport_cleaned.csv",
    index=False
)

# --------------------------------------------------
# Create duplicate-review report
# --------------------------------------------------
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

print("Rows:", len(df))
print("Unique fingerprints:", df["PropertyFingerprint"].nunique())

print(
    "Average listings per property:",
    round(
        len(df) /
        df["PropertyFingerprint"].nunique(),
        2
    )
)