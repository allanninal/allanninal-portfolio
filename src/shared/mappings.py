"""
Consolidated region mappings for country-to-region classification.

This module provides a single source of truth for region mappings used across
all database modules. Use the appropriate mapping based on your dataset's needs.

Mappings available:
- REGION_MAPPING_FULL: Comprehensive mapping (200+ countries)
- REGION_MAPPING_OECD: OECD member countries subset
- get_region(): Helper function with fallback
"""

from typing import Optional


# =============================================================================
# COMPREHENSIVE REGION MAPPING (200+ countries)
# =============================================================================
# Covers most countries worldwide, suitable for:
# - Maddison Project (Economic History)
# - Natural Disasters (EM-DAT)
# - Plastic Waste
# - Any global dataset

REGION_MAPPING_FULL = {
    # Western Europe
    "Austria": "Western Europe",
    "Belgium": "Western Europe",
    "France": "Western Europe",
    "Germany": "Western Europe",
    "Luxembourg": "Western Europe",
    "Netherlands": "Western Europe",
    "Switzerland": "Western Europe",
    "Monaco": "Western Europe",
    "Liechtenstein": "Western Europe",

    # Northern Europe
    "Denmark": "Northern Europe",
    "Finland": "Northern Europe",
    "Iceland": "Northern Europe",
    "Ireland": "Northern Europe",
    "Norway": "Northern Europe",
    "Sweden": "Northern Europe",
    "United Kingdom": "Northern Europe",
    "Estonia": "Northern Europe",
    "Latvia": "Northern Europe",
    "Lithuania": "Northern Europe",
    "Faeroe Islands": "Northern Europe",

    # Southern Europe
    "Greece": "Southern Europe",
    "Italy": "Southern Europe",
    "Portugal": "Southern Europe",
    "Spain": "Southern Europe",
    "Slovenia": "Southern Europe",
    "Croatia": "Southern Europe",
    "Malta": "Southern Europe",
    "Cyprus": "Southern Europe",
    "Serbia": "Southern Europe",
    "Albania": "Southern Europe",
    "Montenegro": "Southern Europe",
    "Bosnia and Herzegovina": "Southern Europe",
    "North Macedonia": "Southern Europe",
    "Macedonia": "Southern Europe",
    "Andorra": "Southern Europe",
    "San Marino": "Southern Europe",

    # Eastern Europe
    "Bulgaria": "Eastern Europe",
    "Poland": "Eastern Europe",
    "Romania": "Eastern Europe",
    "Russia": "Eastern Europe",
    "Ukraine": "Eastern Europe",
    "Belarus": "Eastern Europe",
    "Moldova": "Eastern Europe",
    "Czech Republic": "Eastern Europe",
    "Czechia": "Eastern Europe",
    "Slovakia": "Eastern Europe",
    "Hungary": "Eastern Europe",

    # Central Asia
    "Kazakhstan": "Central Asia",
    "Kyrgyzstan": "Central Asia",
    "Tajikistan": "Central Asia",
    "Turkmenistan": "Central Asia",
    "Uzbekistan": "Central Asia",
    "Mongolia": "Central Asia",
    "Georgia": "Central Asia",
    "Armenia": "Central Asia",
    "Azerbaijan": "Central Asia",

    # North America
    "Canada": "North America",
    "United States": "North America",
    "Mexico": "North America",
    "Bermuda": "North America",
    "Greenland": "North America",

    # Central America & Caribbean
    "Belize": "Central America & Caribbean",
    "Costa Rica": "Central America & Caribbean",
    "Cuba": "Central America & Caribbean",
    "Dominican Republic": "Central America & Caribbean",
    "El Salvador": "Central America & Caribbean",
    "Guatemala": "Central America & Caribbean",
    "Haiti": "Central America & Caribbean",
    "Honduras": "Central America & Caribbean",
    "Jamaica": "Central America & Caribbean",
    "Nicaragua": "Central America & Caribbean",
    "Panama": "Central America & Caribbean",
    "Puerto Rico": "Central America & Caribbean",
    "Trinidad and Tobago": "Central America & Caribbean",
    "Bahamas": "Central America & Caribbean",
    "Barbados": "Central America & Caribbean",
    "Antigua and Barbuda": "Central America & Caribbean",
    "Dominica": "Central America & Caribbean",
    "Grenada": "Central America & Caribbean",
    "Saint Kitts and Nevis": "Central America & Caribbean",
    "Saint Lucia": "Central America & Caribbean",
    "Saint Vincent and the Grenadines": "Central America & Caribbean",
    "Aruba": "Central America & Caribbean",
    "Cayman Islands": "Central America & Caribbean",
    "Curacao": "Central America & Caribbean",
    "Guadeloupe": "Central America & Caribbean",
    "Martinique": "Central America & Caribbean",
    "Netherlands Antilles": "Central America & Caribbean",
    "Sint Maarten (Dutch part)": "Central America & Caribbean",
    "Turks and Caicos Islands": "Central America & Caribbean",
    "British Virgin Islands": "Central America & Caribbean",
    "Anguilla": "Central America & Caribbean",
    "Montserrat": "Central America & Caribbean",
    "United States Virgin Islands": "Central America & Caribbean",

    # South America (Latin America)
    "Argentina": "South America",
    "Brazil": "South America",
    "Chile": "South America",
    "Colombia": "South America",
    "Ecuador": "South America",
    "Guyana": "South America",
    "Peru": "South America",
    "Suriname": "South America",
    "Uruguay": "South America",
    "Venezuela": "South America",
    "Bolivia": "South America",
    "Paraguay": "South America",
    "French Guiana": "South America",

    # East Asia
    "China": "East Asia",
    "Japan": "East Asia",
    "South Korea": "East Asia",
    "North Korea": "East Asia",
    "Taiwan": "East Asia",
    "Hong Kong": "East Asia",
    "Macao": "East Asia",

    # Southeast Asia
    "Brunei": "Southeast Asia",
    "Cambodia": "Southeast Asia",
    "Indonesia": "Southeast Asia",
    "Malaysia": "Southeast Asia",
    "Myanmar": "Southeast Asia",
    "Philippines": "Southeast Asia",
    "Singapore": "Southeast Asia",
    "Thailand": "Southeast Asia",
    "Vietnam": "Southeast Asia",
    "Laos": "Southeast Asia",
    "Timor-Leste": "Southeast Asia",
    "East Timor": "Southeast Asia",

    # South Asia
    "Bangladesh": "South Asia",
    "India": "South Asia",
    "Maldives": "South Asia",
    "Pakistan": "South Asia",
    "Sri Lanka": "South Asia",
    "Nepal": "South Asia",
    "Bhutan": "South Asia",
    "Afghanistan": "South Asia",

    # Middle East
    "Bahrain": "Middle East",
    "Iran": "Middle East",
    "Iraq": "Middle East",
    "Israel": "Middle East",
    "Jordan": "Middle East",
    "Kuwait": "Middle East",
    "Lebanon": "Middle East",
    "Oman": "Middle East",
    "Qatar": "Middle East",
    "Saudi Arabia": "Middle East",
    "Syria": "Middle East",
    "Turkey": "Middle East",
    "United Arab Emirates": "Middle East",
    "Yemen": "Middle East",
    "Palestine": "Middle East",

    # North Africa
    "Algeria": "North Africa",
    "Egypt": "North Africa",
    "Libya": "North Africa",
    "Morocco": "North Africa",
    "Tunisia": "North Africa",
    "Sudan": "North Africa",

    # Sub-Saharan Africa
    "Angola": "Sub-Saharan Africa",
    "Benin": "Sub-Saharan Africa",
    "Botswana": "Sub-Saharan Africa",
    "Burkina Faso": "Sub-Saharan Africa",
    "Burundi": "Sub-Saharan Africa",
    "Cameroon": "Sub-Saharan Africa",
    "Cape Verde": "Sub-Saharan Africa",
    "Central African Republic": "Sub-Saharan Africa",
    "Chad": "Sub-Saharan Africa",
    "Comoros": "Sub-Saharan Africa",
    "Congo": "Sub-Saharan Africa",
    "Democratic Republic of Congo": "Sub-Saharan Africa",
    "Republic of Congo": "Sub-Saharan Africa",
    "Cote d'Ivoire": "Sub-Saharan Africa",
    "Djibouti": "Sub-Saharan Africa",
    "Equatorial Guinea": "Sub-Saharan Africa",
    "Eritrea": "Sub-Saharan Africa",
    "Eswatini": "Sub-Saharan Africa",
    "Swaziland": "Sub-Saharan Africa",
    "Ethiopia": "Sub-Saharan Africa",
    "Gabon": "Sub-Saharan Africa",
    "Gambia": "Sub-Saharan Africa",
    "Ghana": "Sub-Saharan Africa",
    "Guinea": "Sub-Saharan Africa",
    "Guinea-Bissau": "Sub-Saharan Africa",
    "Kenya": "Sub-Saharan Africa",
    "Lesotho": "Sub-Saharan Africa",
    "Liberia": "Sub-Saharan Africa",
    "Madagascar": "Sub-Saharan Africa",
    "Malawi": "Sub-Saharan Africa",
    "Mali": "Sub-Saharan Africa",
    "Mauritania": "Sub-Saharan Africa",
    "Mauritius": "Sub-Saharan Africa",
    "Mayotte": "Sub-Saharan Africa",
    "Mozambique": "Sub-Saharan Africa",
    "Namibia": "Sub-Saharan Africa",
    "Niger": "Sub-Saharan Africa",
    "Nigeria": "Sub-Saharan Africa",
    "Reunion": "Sub-Saharan Africa",
    "Rwanda": "Sub-Saharan Africa",
    "Sao Tome and Principe": "Sub-Saharan Africa",
    "Senegal": "Sub-Saharan Africa",
    "Seychelles": "Sub-Saharan Africa",
    "Sierra Leone": "Sub-Saharan Africa",
    "Somalia": "Sub-Saharan Africa",
    "South Africa": "Sub-Saharan Africa",
    "South Sudan": "Sub-Saharan Africa",
    "Tanzania": "Sub-Saharan Africa",
    "Togo": "Sub-Saharan Africa",
    "Uganda": "Sub-Saharan Africa",
    "Zambia": "Sub-Saharan Africa",
    "Zimbabwe": "Sub-Saharan Africa",

    # Oceania
    "Australia": "Oceania",
    "Fiji": "Oceania",
    "French Polynesia": "Oceania",
    "Kiribati": "Oceania",
    "Marshall Islands": "Oceania",
    "Micronesia": "Oceania",
    "Micronesia (country)": "Oceania",
    "Nauru": "Oceania",
    "New Caledonia": "Oceania",
    "New Zealand": "Oceania",
    "Niue": "Oceania",
    "Palau": "Oceania",
    "Papua New Guinea": "Oceania",
    "Samoa": "Oceania",
    "Solomon Islands": "Oceania",
    "Tonga": "Oceania",
    "Tuvalu": "Oceania",
    "Vanuatu": "Oceania",
    "Cook Islands": "Oceania",
    "Guam": "Oceania",
    "Northern Mariana Islands": "Oceania",
    "American Samoa": "Oceania",
    "Wallis and Futuna": "Oceania",
    "Tokelau": "Oceania",
}


# =============================================================================
# OECD REGION MAPPING (44 countries)
# =============================================================================
# Focused mapping for OECD datasets:
# - Life Expectancy
# - World Happiness Report

REGION_MAPPING_OECD = {
    # Western Europe
    "Austria": "Western Europe",
    "Belgium": "Western Europe",
    "France": "Western Europe",
    "Germany": "Western Europe",
    "Luxembourg": "Western Europe",
    "Netherlands": "Western Europe",
    "Switzerland": "Western Europe",

    # Northern Europe
    "Denmark": "Northern Europe",
    "Finland": "Northern Europe",
    "Iceland": "Northern Europe",
    "Ireland": "Northern Europe",
    "Norway": "Northern Europe",
    "Sweden": "Northern Europe",
    "United Kingdom": "Northern Europe",
    "Estonia": "Northern Europe",
    "Latvia": "Northern Europe",
    "Lithuania": "Northern Europe",

    # Southern Europe
    "Greece": "Southern Europe",
    "Italy": "Southern Europe",
    "Portugal": "Southern Europe",
    "Spain": "Southern Europe",
    "Slovenia": "Southern Europe",

    # Eastern Europe
    "Czech Republic": "Eastern Europe",
    "Hungary": "Eastern Europe",
    "Poland": "Eastern Europe",
    "Slovakia": "Eastern Europe",
    "Russia": "Eastern Europe",

    # North America
    "Canada": "North America",
    "United States": "North America",
    "Mexico": "North America",

    # Latin America
    "Brazil": "Latin America",
    "Chile": "Latin America",
    "Colombia": "Latin America",
    "Costa Rica": "Latin America",

    # East Asia
    "China": "East Asia",
    "Japan": "East Asia",
    "South Korea": "East Asia",

    # South Asia
    "India": "South Asia",

    # Southeast Asia
    "Indonesia": "Southeast Asia",

    # Middle East
    "Israel": "Middle East",
    "Turkey": "Middle East",

    # Oceania
    "Australia": "Oceania",
    "New Zealand": "Oceania",

    # Africa
    "South Africa": "Sub-Saharan Africa",
}


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def get_region(
    country: str,
    mapping: dict = None,
    default: str = "Other"
) -> str:
    """
    Get region for a country with fallback support.

    Args:
        country: Country name to look up.
        mapping: Region mapping to use. Defaults to REGION_MAPPING_FULL.
        default: Default region if country not found.

    Returns:
        Region name or default value.

    Example:
        >>> get_region("Japan")
        'East Asia'
        >>> get_region("Unknown Country")
        'Other'
    """
    if mapping is None:
        mapping = REGION_MAPPING_FULL
    return mapping.get(country, default)


def add_region_column(
    df,
    country_column: str = "entity",
    region_column: str = "region",
    mapping: dict = None
):
    """
    Add region column to a DataFrame based on country column.

    Args:
        df: pandas DataFrame with country data.
        country_column: Name of column containing country names.
        region_column: Name of new column to create with regions.
        mapping: Region mapping to use. Defaults to REGION_MAPPING_FULL.

    Returns:
        DataFrame with new region column added.

    Example:
        >>> df = add_region_column(df, country_column='Country')
    """
    if mapping is None:
        mapping = REGION_MAPPING_FULL
    df[region_column] = df[country_column].map(mapping).fillna("Other")
    return df


def get_all_regions(mapping: dict = None) -> list:
    """
    Get list of all unique regions in a mapping.

    Args:
        mapping: Region mapping to analyze. Defaults to REGION_MAPPING_FULL.

    Returns:
        Sorted list of unique region names.
    """
    if mapping is None:
        mapping = REGION_MAPPING_FULL
    return sorted(set(mapping.values()))


def get_countries_in_region(
    region: str,
    mapping: dict = None
) -> list:
    """
    Get all countries in a specific region.

    Args:
        region: Region name to look up.
        mapping: Region mapping to use. Defaults to REGION_MAPPING_FULL.

    Returns:
        Sorted list of countries in that region.
    """
    if mapping is None:
        mapping = REGION_MAPPING_FULL
    return sorted([
        country for country, r in mapping.items()
        if r == region
    ])


# Alias for backwards compatibility
REGION_MAPPING = REGION_MAPPING_FULL
