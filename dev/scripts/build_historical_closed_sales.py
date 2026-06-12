import pandas as pd
import re

# --------------------------------------------------
# Load historical closed-sales export
# --------------------------------------------------

df = pd.read_csv(
    "raw/ClosedInceptionTo2026-06-05.csv",
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

    if value in ["0", "0000", "."]:
        return ""

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

    street_name = re.sub(r"^AV\s+", "AVENIDA ", street_name)
    street_name = re.sub(r"^AVE\s+", "AVENIDA ", street_name)
    street_name = re.sub(r"^BLVD\s+", "BOULEVARD ", street_name)
    street_name = re.sub(r"^BVLD\s+", "BOULEVARD ", street_name)

    street_name = re.sub(r"^CALLE\s+", "", street_name)
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

    # Historical MLS exception:
    # Older records sometimes store the development/project name
    # in Property Name instead of Development Name.
    property_name = normalize_text(row["Property Name"])

    if property_name:
        return property_name

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
    if pd.isna(directions):
        return ""

    text = normalize_text(directions)

    patterns = [
        r"\bUNIT\s+([A-Z]?\d+[A-Z]?)\b",
        r"\bCONDO\s+([A-Z]?\d+[A-Z]?)\b",
    ]

    for pattern in patterns:
        match = re.search(pattern, text)

        if match:
            return match.group(1)

    return ""


def fill_missing_or_non_numeric_unit(row):
    unit = row["NormalizedUnit"]

    if re.search(r"\d", unit):
        if unit == "1":
            derived = derive_unit_from_directions(row["Directions"])

            if derived:
                return derived

        return unit

    derived = derive_unit_from_ncn(
        normalize_text(row["NO_COMMON_NAME"])
    )

    if derived:
        return derived

    return unit


def build_normalized_building(row):
    development = row["NormalizedDevelopment"]
    street_name = normalize_text(row["Street Name"])

    # MLS exception:
    # Quinta San Miguel Canal has multiple towers with repeated unit numbers.
    # MLS stores tower number at the end of Street Name:
    # "Paseo de los Cocoteros Torre 5"
    if development == "QUINTA SAN MIGUEL CANAL":
        match = re.search(r"\bTORRE\s+(\d+)\b", street_name)

        if match:
            return "TORRE " + match.group(1)

    return ""


def build_property_fingerprint(row):
    if (
        row["NormalizedDevelopment"]
        and row["NormalizedBuilding"]
        and row["NormalizedUnit"]
    ):
        return (
            row["NormalizedDevelopment"]
            + "|"
            + row["NormalizedBuilding"]
            + "|"
            + row["NormalizedUnit"]
        )

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

df["NormalizedBuilding"] = (
    df.apply(build_normalized_building, axis=1)
)

df["PropertyFingerprint"] = (
    df.apply(build_property_fingerprint, axis=1)
)

# --------------------------------------------------
# Add historical closed-sales reporting fields
# --------------------------------------------------

df["SoldDateParsed"] = pd.to_datetime(
    df["Sold Date"],
    errors="coerce"
)

df["SaleYear"] = df["SoldDateParsed"].dt.year
df["SaleMonth"] = df["SoldDateParsed"].dt.month

df["SaleYearMonth"] = (
    df["SoldDateParsed"]
    .dt.to_period("M")
    .astype(str)
)

df["SoldPricePerM2"] = (
    df["Sold Price USD$"] /
    df["Condo M2"]
)

df.loc[
    df["Condo M2"] <= 0,
    "SoldPricePerM2"
] = pd.NA

# --------------------------------------------------
# Export historical closed-sales dataset
# --------------------------------------------------

df.to_csv(
    "cleaned/historical_closed_sales.csv",
    index=False
)

# --------------------------------------------------
# Create duplicate-review report for closed sales
# --------------------------------------------------

duplicate_fingerprints = df["PropertyFingerprint"].value_counts()

duplicates_review = (
    df[df["PropertyFingerprint"].duplicated(keep=False)]
    .sort_values("PropertyFingerprint")
)

duplicates_review.to_csv(
    "cleaned/historical_closed_sales_duplicates_review.csv",
    index=False
)

# --------------------------------------------------
# Summary output
# --------------------------------------------------

print("Historical closed sales build complete.")
print("Rows:", len(df))
print("Unique fingerprints:", df["PropertyFingerprint"].nunique())
print("Output written to: cleaned/historical_closed_sales.csv")
print("Duplicate review written to: cleaned/historical_closed_sales_duplicates_review.csv")

print("\nTop duplicate fingerprints:")
print(duplicate_fingerprints[duplicate_fingerprints > 1].head(25))