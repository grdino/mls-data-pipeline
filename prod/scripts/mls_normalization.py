"""
Shared MLS normalization functions.

Used by:
- clean_current_mls.py
- build_historical_sales.py

The goal is to keep all fingerprinting, unit cleanup, tax ID cleanup,
and MLS exception logic in one place.
"""

import re
import pandas as pd


# --------------------------------------------------
# Basic normalization helpers
# --------------------------------------------------

def normalize_unit(value):
    """Normalize MLS Unit # values for matching/fingerprinting."""

    if pd.isna(value):
        return ""

    value = str(value).upper().strip()

    value = re.sub(
        r"\b(SUITE|UNIT|APT|APARTMENT|DEPTO|DEPARTAMENTO)\b",
        "",
        value,
    )

    value = value.replace("|", "")
    value = value.replace("#", "")
    value = " ".join(value.split())

    # Normalize house labels such as CASA 12, HOUSE 12, VILLA 12.
    value = re.sub(r"^(CASA|HOUSE|VILLA)\s+(\d+)$", r"\2", value)

    # Normalize penthouse abbreviations.
    value = value.replace("PH ", "PH")
    value = value.replace("P H ", "PH")
    value = re.sub(r"^(\d+)\s+PH$", r"\1PH", value)

    # Normalize values like A-101, A 101, 101-A, 101 A.
    value = re.sub(r"^([A-Z])[\s\-]+(\d+)$", r"\1\2", value)
    value = re.sub(r"^(\d+)[\s\-]+([A-Z])$", r"\1\2", value)

    return value.strip()


def normalize_tax_id(value):
    """Normalize Tax ID values and remove placeholder values."""

    if pd.isna(value):
        return ""

    value = str(value).upper().strip()
    value = value.replace("-", "")
    value = value.replace(" ", "")

    # MLS placeholder values that should not be used for matching.
    if value in ["0", "0000", "."]:
        return ""

    return value


def normalize_text(value):
    """Normalize general text fields for matching."""

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


def get_field(row, field_name):
    """Safely get a field from a pandas row; return blank if missing."""

    if field_name not in row.index:
        return ""

    return row[field_name]


# --------------------------------------------------
# Derived normalized fields
# --------------------------------------------------

def build_normalized_address(row):
    """Build a normalized address from street number/name/suffix."""

    street_number = normalize_text(get_field(row, "Street Number"))
    street_name = normalize_text(get_field(row, "Street Name"))
    street_suffix = normalize_text(get_field(row, "Street Suffix"))

    # Normalize common street abbreviations.
    street_name = re.sub(r"^AV\s+", "AVENIDA ", street_name)
    street_name = re.sub(r"^AVE\s+", "AVENIDA ", street_name)
    street_name = re.sub(r"^BLVD\s+", "BOULEVARD ", street_name)
    street_name = re.sub(r"^BVLD\s+", "BOULEVARD ", street_name)

    # Remove CALLE prefixes.
    street_name = re.sub(r"^CALLE\s+", "", street_name)
    street_name = re.sub(r"^C\.\s+", "", street_name)
    street_name = re.sub(r"^C\s+", "", street_name)

    address = " ".join(
        part for part in [street_number, street_name, street_suffix]
        if part
    )

    return address


def build_normalized_development(row, use_property_name_fallback=True):
    """
    Build normalized development/project name.

    Priority:
    1. Development Name
    2. Property Name, if allowed and present
    3. NO_COMMON_NAME with unit removed
    """

    development = normalize_text(get_field(row, "Development Name"))

    if development:
        return development

    if use_property_name_fallback:
        property_name = normalize_text(get_field(row, "Property Name"))

        if property_name:
            return property_name

    ncn = normalize_text(get_field(row, "NO_COMMON_NAME"))
    unit = get_field(row, "NormalizedUnit")

    if ncn and unit:
        ncn = ncn.replace(unit, "")
        ncn = " ".join(ncn.split())

    return ncn


# --------------------------------------------------
# MLS data exception helpers
# --------------------------------------------------

def derive_unit_from_ncn(ncn):
    """Derive unit from NO_COMMON_NAME if it contains exactly one number."""

    if not ncn:
        return ""

    matches = re.findall(r"\d+", ncn)

    if len(matches) == 1:
        return matches[0]

    return ""


def derive_unit_from_directions(directions):
    """
    Derive unit from Directions.

    MLS exception:
    Some condo projects store Unit # as "1" for all units.
    The actual condo number may appear in Directions:

        "unit 201 floor 2"
        "unit 102 floor 1"
        "condo 304"
    """

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
    """Fill or improve NormalizedUnit using MLS exception rules."""

    unit = get_field(row, "NormalizedUnit")

    # Normal case: unit already contains a number.
    if re.search(r"\d", unit):

        # MLS exception: Unit # stored as "1" for many units.
        # Check Directions for a more specific unit number.
        if unit == "1":
            derived = derive_unit_from_directions(get_field(row, "Directions"))

            if derived:
                return derived

        return unit

    # MLS exception: unit stored in NO_COMMON_NAME.
    derived = derive_unit_from_ncn(
        normalize_text(get_field(row, "NO_COMMON_NAME"))
    )

    if derived:
        return derived

    return unit


def build_normalized_building(row):
    """
    Build normalized building/tower value where needed.

    MLS exception:
    Quinta San Miguel Canal has multiple towers with repeated unit numbers.
    MLS stores the tower number at the end of Street Name:

        "Paseo de los Cocoteros Torre 5"
    """

    development = get_field(row, "NormalizedDevelopment")
    street_name = normalize_text(get_field(row, "Street Name"))

    if development == "QUINTA SAN MIGUEL CANAL":
        match = re.search(r"\bTORRE\s+(\d+)\b", street_name)

        if match:
            return "TORRE " + match.group(1)

    return ""


# --------------------------------------------------
# Fingerprint generation
# --------------------------------------------------

def build_property_fingerprint(row, include_building=True):
    """
    Create the primary matching key used for duplicate detection.

    Priority:
    1. Development + Building + Unit, when include_building=True
    2. Development + Unit
    3. Tax ID
    4. Address
    """

    if (
        include_building
        and get_field(row, "NormalizedDevelopment")
        and get_field(row, "NormalizedBuilding")
        and get_field(row, "NormalizedUnit")
    ):
        return (
            get_field(row, "NormalizedDevelopment")
            + "|"
            + get_field(row, "NormalizedBuilding")
            + "|"
            + get_field(row, "NormalizedUnit")
        )

    if get_field(row, "NormalizedDevelopment") and get_field(row, "NormalizedUnit"):
        return (
            get_field(row, "NormalizedDevelopment")
            + "|"
            + get_field(row, "NormalizedUnit")
        )

    if get_field(row, "NormalizedTaxID"):
        return get_field(row, "NormalizedTaxID")

    return get_field(row, "NormalizedAddress")


def apply_property_normalization(
    df,
    use_property_name_fallback=True,
    include_building=True,
):
    """
    Apply all shared normalization rules to an MLS dataframe.

    Returns the same dataframe with these fields added:
    - NormalizedUnit
    - NormalizedTaxID
    - NormalizedDevelopment
    - NormalizedAddress
    - NormalizedBuilding
    - PropertyFingerprint
    """

    df["NormalizedUnit"] = df["Unit #"].apply(normalize_unit)

    df["NormalizedUnit"] = df.apply(
        fill_missing_or_non_numeric_unit,
        axis=1,
    )

    df["NormalizedTaxID"] = df["Tax ID Number"].apply(normalize_tax_id)

    df["NormalizedDevelopment"] = df.apply(
        lambda row: build_normalized_development(
            row,
            use_property_name_fallback=use_property_name_fallback,
        ),
        axis=1,
    )

    df["NormalizedAddress"] = df.apply(
        build_normalized_address,
        axis=1,
    )

    df["NormalizedBuilding"] = df.apply(
        build_normalized_building,
        axis=1,
    )

    df["PropertyFingerprint"] = df.apply(
        lambda row: build_property_fingerprint(
            row,
            include_building=include_building,
        ),
        axis=1,
    )

    return df


# --------------------------------------------------
# Duplicate review helper
# --------------------------------------------------

def build_duplicate_review(df):
    """Return duplicate fingerprint counts and duplicate-review dataframe."""

    duplicate_fingerprints = df["PropertyFingerprint"].value_counts()

    duplicates_review = (
        df[df["PropertyFingerprint"].duplicated(keep=False)]
        .sort_values("PropertyFingerprint")
    )

    return duplicate_fingerprints, duplicates_review
