from typing import Literal, Optional

from pydantic import BaseModel, Field


class EmissionEntry(BaseModel):
    """A single emission source entry (e.g. diesel combustion, electricity consumption)."""

    source: str = Field(
        description=(
            "The activity or fuel that generated the emission. "
            "E.g. 'diesel combustion', 'grid electricity', 'LPG combustion'. "
            "Never merge multiple sources into one entry."
        )
    )

    fuel_or_activity: str = Field(
        description=(
            "Specific fuel or activity type. "
            "E.g. 'diesel', 'electricity', 'LPG', 'natural_gas'. Use lowercase."
        )
    )

    quantity: float = Field(
        ge=0,
        description="Amount of fuel consumed or activity performed, in the original unit as stated in the source."
    )

    unit: str = Field(
        description="Unit of quantity before conversion. E.g. 'liters', 'kWh', 'm3', 'kg'."
    )

    emission_factor: float = Field(
        ge=0,
        description=(
            "Emission factor applied to convert quantity to CO₂e. "
            "E.g. 2.68 kg CO₂e/liter for diesel (IPCC 2006), 0.6 kg CO₂e/kWh for PH grid electricity. "
            "Always populate — never leave at 0 unless the factor is genuinely zero."
        )
    )

    emission_factor_unit: str = Field(
        description="Unit of the emission factor. E.g. 'kg CO2e/liter', 'kg CO2e/kWh'."
    )

    emissions_kg_co2e: float = Field(
        ge=0,
        description=(
            "Calculated GHG emissions in kilograms CO₂e. "
            "Must equal quantity * emission_factor. Always compute — never leave at 0 unless quantity is zero."
        )
    )

    ghg_gases_included: list[str] = Field(
        description=(
            "List of GHG gases included in this entry. "
            "E.g. ['CO2'], ['CO2', 'CH4', 'N2O']. "
            "Use standard chemical notation."
        )
    )

    is_biogenic: bool = Field(
        default=False,
        description="True if this emission is biogenic CO₂ (e.g. from biomass burning). Must be reported separately per GRI 305."
    )

    confidence: float = Field(
        default=0.8,
        ge=0,
        le=1,
        description=(
            "How explicitly the value was stated. "
            "1.0 = exact figure from a document. "
            "0.7-0.9 = estimated or approximate. "
            "0.5-0.6 = vague or inferred. "
            "Below 0.5 = handwritten, unclear, or conflicting records."
        )
    )



class EmissionFactorMetadata(BaseModel):
    """Metadata about the emission factors and methodology used."""

    source: str = Field(
        default="IPCC Default Emission Factors 2006",
        description=(
            "Reference standard for emission factors used. "
            "E.g. 'IPCC Default Emission Factors 2006', 'Philippine DOE Grid Emission Factor 2023'. "
            "Always populate even if not formally documented — use the standard that matches the factors applied."
        )
    )

    gwp_source: Optional[str] = Field(
        default=None,
        description="Source of Global Warming Potential (GWP) rates used. E.g. 'IPCC AR5'. Set to null if not mentioned."
    )

    consolidation_approach: Optional[str] = Field(
        default=None,
        description=(
            "Approach used to consolidate emissions across the organization. "
            "Use 'operational_control', 'financial_control', or 'equity_share'. "
            "Set to null if not mentioned."
        )
    )

    calculation_methodology: Optional[str] = Field(
        default=None,
        description=(
            "Method used to calculate emissions. "
            "E.g. 'location-based', 'market-based'. "
            "Required for Scope 2. Set to null if not mentioned."
        )
    )




class Omission305(BaseModel):
    field_name: Literal[
        "scope1_entries",
        "scope1_total_kg_co2e",
        "scope1_biogenic_kg_co2",
        "scope2_entries",
        "scope2_location_based_kg_co2e",
        "scope2_market_based_kg_co2e",
        "scope2_biogenic_kg_co2",
        "scope3_total_kg_co2e",
        "scope3_categories_included",
        "scope3_biogenic_kg_co2",
        "employee_count",
        "revenue",
        "intensity_denominator",
        "intensity_scopes_included",
        "ghg_reduction_kg_co2e",
        "reduction_scopes_included",
        "baseline_year",
        "ods_kg_cfc11e",
        "ods_substances",
        "nox_kg",
        "sox_kg",
        "voc_kg",
        "pm_kg",
        "emission_factor_metadata",
        "base_year"
    ] = Field(
        description=(
            "The exact field name that could not be populated. "
            "Must be one of the defined GRI 302 fields. "
            "Do not invent field names outside this list."
        )
    )

    reason: str = Field(
        description=(
            "Specific reason why this field is absent. "
            "Reference the source material directly — e.g. 'organization stated they have no baseline year', "
            "'document only covers electricity, no fuel records provided'. "
            "Do not use generic reasons like 'not found' or 'missing'."
        )
    )