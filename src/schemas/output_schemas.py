from __future__ import annotations

from enum import Enum
from pydantic import BaseModel, ConfigDict, Field
from typing import Dict, Literal, Optional, Union, List
from src.schemas.MetricsSchemas.GRI_302_Metrics import EnergyEntry, ConversionFactors, Omission302
from src.schemas.MetricsSchemas.GRI_305_Metrics import EmissionEntry, EmissionFactorMetadata, Omission305
from src.schemas.MetricsSchemas.GRI_401_Metrics import BenefitEntry, BreakdownByAgeGroup, BreakdownByGender, BreakdownByRegion, Omission401, GenderRate, ParentalLeaveByGender



# ============================================================================
# UNIFIED GRI 302 (ENERGY) SCHEMA
# ============================================================================

class AIExtracted_GRI_302(BaseModel):
    """
    Unified schema for GRI 302 (Energy) standard covering all sub-standards.
    
    This schema consolidates data points from:
    - GRI 302-1: Energy Consumption Within the Organization
    - GRI 302-2: Energy Consumption Outside of the Organization
    - GRI 302-3: Energy Intensity
    - GRI 302-4: Reduction of Energy Consumption
    - GRI 302-5: Reductions in Energy Requirements of Sold Products and Services
    
    All fields are optional to accommodate partial data extraction.
    Use omitted_fields to track explanation for missing data.
    """

    # ---- GRI 302-1: Energy Consumption Within Organization ----
    energy_entries: Optional[List[EnergyEntry]] = Field(
        default=None,
        description=(
            "Each distinct energy source as a separate entry (e.g. electricity, diesel, LPG, solar). "
            "Always extract even if values are approximate. Use confidence < 0.8 for estimates or handwritten records. "
            "Do not merge multiple sources into one entry."
        )
    )
    
    total_energy_mj: Optional[float] = Field(
        default=None,
        ge=0,
        description=(
            "Sum of converted_mj across ALL energy_entries. "
            "Must equal renewable_energy_mj + non_renewable_energy_mj. "
            "Always compute this if energy_entries is present — never leave null when entries exist."
        )
    )
    
    renewable_energy_mj: Optional[float] = Field(
        default=None,
        ge=0,
        description=(
            "Sum of converted_mj from energy_entries where is_renewable=true. "
            "Set to 0.0 (not null) if no renewable sources were mentioned."
        )
    )
    
    non_renewable_energy_mj: Optional[float] = Field(
        default=None,
        ge=0,
        description=(
            "Sum of converted_mj from energy_entries where is_renewable=false. "
            "Set to 0.0 (not null) if no non-renewable sources were mentioned."
        )
    )

    # ---- GRI 302-2: Energy Consumption Outside Organization ----
    external_energy_mj: Optional[float] = Field(
        default=None,
        ge=0,
        description=(
            "Energy from purchased electricity, district heating/cooling, or steam — i.e. energy generated outside "
            "the organization's operational boundary. This is a subset of energy_entries, not additional energy. "
            "Set to null only if no purchased/external energy was mentioned."
        )
    )

    # ---- GRI 302-3: Energy Intensity ----
    employee_count: Optional[int] = Field(
        default=None,
        ge=0,
        description=(
            "Total headcount used as the intensity denominator. "
            "Use the stated number even if part-time status is ambiguous; reflect ambiguity via low confidence in "
            "the related energy entry instead. Do not average or adjust."
        )
    )
    
    revenue: Optional[float] = Field(
        default=None,
        ge=0,
        description="Organization revenue in local currency, used as an alternative intensity denominator. Set to null if not mentioned."
    )
    
    intensity_denominator: Optional[str] = Field(
        default=None,
        description=(
            "The denominator used for energy intensity (GRI 302-3). "
            "Use 'per_employee' if headcount is the basis, 'per_revenue_unit' if revenue is the basis. "
            "Set to null if the intensity method was not mentioned or was unclear."
        )
    )

    # ---- GRI 302-4: Energy Reduction ----
    energy_reduction_mj: Optional[float] = Field(
        default=None,
        description=(
            "Measured reduction in energy consumption vs a baseline year (MJ). "
            "Set to null — NOT 0 — if the organization has no baseline to compare against or explicitly states "
            "they cannot yet measure reductions. Only set to 0.0 if a comparison was made and no reduction was found."
        )
    )
    
    baseline_year: Optional[str] = Field(
        default=None,
        description=(
            "The year used as the baseline for reduction calculations (YYYY). "
            "Set to null if the organization has not established a baseline or is in early tracking stages."
        )
    )

    # ---- GRI 302-5: Product Energy Reduction ----
    product_energy_reduction_mj: Optional[float] = Field(
        default=None,
        ge=0,
        description="Energy reduction achieved in sold products or services vs baseline (MJ). Set to null if not mentioned."
    )

    # ---- Metadata ----
    conversion_factors: Optional[ConversionFactors] = Field(
        default=None,
        description=(
            "Conversion factors applied to standardize energy units to MJ. "
            "Always populate this if any unit conversion was performed, even if the source was not formally documented. "
            "Use standard defaults: electricity 3.6 MJ/kWh, diesel 36.54 MJ/liter (IPCC 2006). "
            "Only set to null if no conversions were performed at all."
        )
    )
    
    base_year: Optional[str] = Field(
        default=None,
        description="The reporting period year (YYYY). Extract from context (e.g. 'February 2025' → '2025'). Set to null only if no time reference exists."
    )

    # ---- Explainability ----
    omitted_fields: Optional[list[Omission302]] = Field(
        default_factory=list,
        description=(
            "List of fields that could not be populated, each with a field_name and a specific reason. "
            "Only include fields that are genuinely absent from the input. "
            "Do not list fields that were set to 0.0 or a computed value."
        )
    )

# ============================================================================
# UNIFIED GRI 302 (ENERGY) SCHEMA
# ============================================================================



# ============================================================================
# UNIFIED GRI 305 (EMISSION) SCHEMA
# ============================================================================

class AIExtracted_GRI_305(BaseModel):
    """
    Unified schema for GRI 305 (Emissions) standard covering all sub-standards.

    This schema consolidates data points from:
    - GRI 305-1: Direct (Scope 1) GHG Emissions
    - GRI 305-2: Energy Indirect (Scope 2) GHG Emissions
    - GRI 305-3: Other Indirect (Scope 3) GHG Emissions
    - GRI 305-4: GHG Emissions Intensity
    - GRI 305-5: Reduction of GHG Emissions
    - GRI 305-6: Emissions of Ozone-Depleting Substances (ODS)
    - GRI 305-7: Nitrogen Oxides, Sulfur Oxides, and Other Air Emissions

    All fields are optional to accommodate partial data extraction.
    Use omitted_fields to track explanations for missing data.
    """

    # ---- GRI 305-1: Scope 1 (Direct) Emissions ----
    scope1_entries: Optional[list[EmissionEntry]] = Field(
        default=None,
        description=(
            "Each direct emission source as a separate entry (e.g. diesel generator, company vehicles, LPG). "
            "Always extract even if values are approximate. One entry per fuel/activity type."
        )
    )

    scope1_total_kg_co2e: Optional[float] = Field(
        default=None,
        ge=0,
        description=(
            "Total Scope 1 (direct) GHG emissions in kilograms CO₂e. "
            "Must equal the sum of emissions_kg_co2e across all scope1_entries. "
            "Always compute if scope1_entries is present — never leave null when entries exist."
        )
    )

    scope1_biogenic_kg_co2: Optional[float] = Field(
        default=None,
        ge=0,
        description="Biogenic CO₂ emissions from Scope 1 sources in kilograms, reported separately per GRI 305. Set to null if no biogenic sources exist."
    )

    # ---- GRI 305-2: Scope 2 (Indirect) Emissions ----
    scope2_entries: Optional[list[EmissionEntry]] = Field(
        default=None,
        description=(
            "Each indirect emission source from purchased energy as a separate entry (e.g. grid electricity, purchased steam). "
            "One entry per energy type."
        )
    )

    scope2_location_based_kg_co2e: Optional[float] = Field(
        default=None,
        ge=0,
        description=(
            "Total Scope 2 emissions using the location-based method in kilograms CO₂e. "
            "Must equal the sum of emissions_kg_co2e across scope2_entries. "
            "Always compute if scope2_entries is present."
        )
    )

    scope2_market_based_kg_co2e: Optional[float] = Field(
        default=None,
        ge=0,
        description="Total Scope 2 emissions using the market-based method in kilograms CO₂e. Set to null if not mentioned."
    )

    scope2_biogenic_kg_co2: Optional[float] = Field(
        default=None,
        ge=0,
        description="Biogenic CO₂ from Scope 2 sources in kilograms, reported separately. Set to null if not applicable."
    )

    # ---- GRI 305-3: Scope 3 (Other Indirect) Emissions ----
    scope3_total_kg_co2e: Optional[float] = Field(
        default=None,
        ge=0,
        description="Total Scope 3 GHG emissions in kilograms CO₂e across all reported categories. Set to null if not tracked."
    )

    scope3_categories_included: Optional[list[str]] = Field(
        default=None,
        description=(
            "Scope 3 categories included in the report. "
            "E.g. ['employee commuting', 'upstream transportation', 'waste disposal']. "
            "Set to null if Scope 3 is not tracked."
        )
    )

    scope3_biogenic_kg_co2: Optional[float] = Field(
        default=None,
        ge=0,
        description="Biogenic CO₂ from Scope 3 sources in kilograms, reported separately. Set to null if not applicable."
    )

    # ---- GRI 305-4: GHG Emissions Intensity ----
    employee_count: Optional[int] = Field(
        default=None,
        ge=0,
        description=(
            "Total headcount used as the intensity denominator. "
            "Use the stated number even if part-time status is ambiguous. Do not average or adjust."
        )
    )

    revenue: Optional[float] = Field(
        default=None,
        ge=0,
        description="Organization revenue in local currency, used as an alternative intensity denominator. Set to null if not mentioned."
    )

    intensity_denominator: Optional[str] = Field(
        default=None,
        description=(
            "Denominator used for GHG intensity ratio. "
            "Use 'per_employee' if headcount is the basis, 'per_revenue_unit' if revenue is the basis. "
            "Set to null if not mentioned."
        )
    )

    intensity_scopes_included: Optional[list[str]] = Field(
        default=None,
        description=(
            "Which scopes are included in the intensity calculation. "
            "E.g. ['scope1', 'scope2'] or ['scope1', 'scope2', 'scope3']. "
            "Set to null if not mentioned."
        )
    )

    # ---- GRI 305-5: GHG Reduction ----
    ghg_reduction_kg_co2e: Optional[float] = Field(
        default=None,
        description=(
            "Total GHG emissions reduced vs baseline year in kilograms CO₂e. "
            "Set to null — NOT 0 — if no baseline exists or the organization explicitly states they cannot yet measure reductions. "
            "Only set to 0.0 if a comparison was made and no reduction was found."
        )
    )

    reduction_scopes_included: Optional[list[str]] = Field(
        default=None,
        description=(
            "Which scopes the reduction figure covers. "
            "E.g. ['scope1'], ['scope1', 'scope2']. "
            "Set to null if reduction is not reported."
        )
    )

    baseline_year: Optional[str] = Field(
        default=None,
        description=(
            "Year used as baseline for GHG reduction calculations (YYYY). "
            "Set to null if the organization has not established a baseline or is in early tracking stages."
        )
    )

    # ---- GRI 305-6: Ozone-Depleting Substances ----
    ods_kg_cfc11e: Optional[float] = Field(
        default=None,
        ge=0,
        description="Total production, import, and export of ozone-depleting substances in metric tons CFC-11 equivalent. Set to null if not mentioned."
    )

    ods_substances: Optional[list[str]] = Field(
        default=None,
        description="List of specific ODS substances reported. E.g. ['R-22', 'R-410A']. Set to null if not mentioned."
    )

    # ---- GRI 305-7: Air Emissions ----
    nox_kg: Optional[float] = Field(default=None, ge=0, description="Nitrogen oxides (NOx) emissions in kilograms. Set to null if not mentioned.")
    sox_kg: Optional[float] = Field(default=None, ge=0, description="Sulfur oxides (SOx) emissions in kilograms. Set to null if not mentioned.")
    voc_kg: Optional[float] = Field(default=None, ge=0, description="Volatile organic compounds (VOC) emissions in kilograms. Set to null if not mentioned.")
    pm_kg: Optional[float]  = Field(default=None, ge=0, description="Particulate matter (PM) emissions in kilograms. Set to null if not mentioned.")

    # ---- Metadata ----
    emission_factor_metadata: Optional[EmissionFactorMetadata] = Field(
        default=None,
        description=(
            "Emission factor sources and methodology used across all scopes. "
            "Always populate if any emission calculation was performed, even if source was not formally documented."
        )
    )

    base_year: Optional[str] = Field(
        default=None,
        description="Reporting period year (YYYY). Extract from context (e.g. 'January 2025' → '2025'). Set to null only if no time reference exists."
    )

    # ---- Explainability ----
    omitted_fields: Optional[list[Omission305]] = Field(
        default_factory=list,
        description=(
            "List of fields that could not be populated, each with a field_name and a specific reason. "
            "Only include fields genuinely absent from the input. "
            "Do not list fields set to 0.0 or successfully computed."
        )
    )

# ============================================================================
# UNIFIED GRI 305 (EMISSION) SCHEMA
# ============================================================================





# ============================================================================
# UNIFIED GRI 401 (EMPLOYMENT) SCHEMA
# ============================================================================

class AIExtracted_GRI_401(BaseModel):
    """
    Unified schema for GRI 401 (Employment) standard covering all sub-standards.

    This schema consolidates data points from:
    - GRI 401-1: New Employee Hires and Employee Turnover
    - GRI 401-2: Benefits Provided to Full-Time Employees
    - GRI 401-3: Parental Leave (Optional)

    All fields are optional to accommodate partial data extraction.
    Use omitted_fields to track explanations for missing data.
    """

    # ---- GRI 401-1: New Hires ----
    total_new_hires: Optional[int] = Field(
        default=None,
        ge=0,
        description=(
            "Total number of new employees hired during the reporting period. "
            "Always extract if mentioned — never leave null when a headcount is stated."
        )
    )
 
    new_hire_rate: Optional[float] = Field(
        default=None,
        ge=0,
        description=(
            "New hire rate as a percentage. Formula: (total_new_hires / total_employees) × 100. "
            "Compute this if total_new_hires and employee_count are both present. "
            "Set to null only if neither is available."
        )
    )
 
    new_hires_by_gender: Optional[BreakdownByGender] = Field(
        default=None,
        description=(
            "New hires broken down by gender. "
            "Populate only the genders explicitly mentioned. Set to null if no gender breakdown is provided."
        )
    )
 
    new_hires_by_age_group: Optional[BreakdownByAgeGroup] = Field(
        default=None,
        description=(
            "New hires broken down by age group (under 30, 30–50, over 50). "
            "Set to null if no age breakdown is provided."
        )
    )
 
    new_hires_by_region: Optional[List[BreakdownByRegion]] = Field(
        default=None,
        description=(
            "New hires broken down by region or location of operation. "
            "One entry per region. Set to null if no regional breakdown is provided."
        )
    )
 
    # ---- GRI 401-1: Turnover ----
    total_turnover: Optional[int] = Field(
        default=None,
        ge=0,
        description=(
            "Total number of employees who left during the reporting period. "
            "Always extract if mentioned — never leave null when a count is stated."
        )
    )
 
    turnover_rate: Optional[float] = Field(
        default=None,
        ge=0,
        description=(
            "Employee turnover rate as a percentage. Formula: (total_turnover / total_employees) × 100. "
            "Compute this if total_turnover and employee_count are both present. "
            "Set to null only if neither is available."
        )
    )
 
    turnover_by_gender: Optional[BreakdownByGender] = Field(
        default=None,
        description=(
            "Employees who left broken down by gender. "
            "Populate only the genders explicitly mentioned. Set to null if no gender breakdown is provided."
        )
    )
 
    turnover_by_age_group: Optional[BreakdownByAgeGroup] = Field(
        default=None,
        description=(
            "Employees who left broken down by age group (under 30, 30–50, over 50). "
            "Set to null if no age breakdown is provided."
        )
    )
 
    turnover_by_region: Optional[List[BreakdownByRegion]] = Field(
        default=None,
        description=(
            "Employees who left broken down by region or location of operation. "
            "One entry per region. Set to null if no regional breakdown is provided."
        )
    )
 
    # ---- GRI 401-2: Benefits ----
    benefits: Optional[List[BenefitEntry]] = Field(
        default=None,
        description=(
            "List of benefits and whether they are provided to full-time vs part-time/temporary employees. "
            "One entry per distinct benefit. Do not merge benefits into one entry. "
            "Exclude in-kind benefits (free meals, transport allowance, gym access) per GRI 401-2 guidelines."
        )
    )
 
    significant_location: Optional[str] = Field(
        default=None,
        description=(
            "The significant location of operation where benefits apply. "
            "E.g. 'Quezon City, NCR'. Set to null if not mentioned."
        )
    )
 
    # ---- GRI 401-3: Parental Leave ----
    parental_leave_by_gender: Optional[List[ParentalLeaveByGender]] = Field(
        default=None,
        description=(
            "Parental leave data broken down by gender, covering entitlement, uptake, "
            "return to work, and 12-month retention. One entry per gender. "
            "Set to null if no parental leave was taken or data is unavailable."
        )
    )
 
    return_to_work_rate_by_gender: Optional[List[GenderRate]] = Field(
        default=None,
        description=(
            "Return-to-work rate after parental leave by gender. "
            "Compute as (returned_to_work / took_leave) × 100 if data is available. "
            "Set to null if parental leave data is unavailable."
        )
    )

    retention_rate_by_gender: Optional[List[GenderRate]] = Field(
        default=None,
        description=(
            "12-month retention rate after returning from parental leave, by gender. "
            "Compute as (still_employed_after_12_months / returned_to_work) × 100 if data is available. "
            "Set to null if parental leave data is unavailable."
        )
    )
    
    # ---- Metadata ----
    employee_count: Optional[int] = Field(
        default=None,
        ge=0,
        description=(
            "Total employee headcount at the time of reporting. "
            "Used as the denominator for new_hire_rate and turnover_rate calculations. "
            "Use the stated number even if part-time status is ambiguous."
        )
    )
 
    base_year: Optional[str] = Field(
        default=None,
        description="Reporting period year (YYYY). Extract from context (e.g. 'January 2025' → '2025'). Set to null only if no time reference exists."
    )
 
    # ---- Explainability ----
    omitted_fields: Optional[List[Omission401]] = Field(
        default_factory=list,
        description=(
            "List of fields that could not be populated, each with a field_name and a specific reason. "
            "Only include fields genuinely absent from the input. "
            "Do not list fields set to 0.0 or successfully computed."
        )
    )

# ============================================================================
# UNIFIED GRI 401 (EMPLOYMENT) SCHEMA
# ============================================================================

class ExtractedData(BaseModel):
    """
    Top-level result schema holding a single detected GRI standard with its data.
    
    This model wraps one of the possible GRI extraction schemas and ensures
    type-safe handling of different ESG standards.
    """

    detected_gri: Literal["GRI_302", "GRI_305", "GRI_401"] = Field(
        description="The detected GRI standard/s"
    )
    
    data: AIExtracted_GRI_302 |\
        AIExtracted_GRI_305 |\
        AIExtracted_GRI_401 \
    = Field(
        description="The extracted data matching the detected GRI standard"
    )






# =========================
# Output Schema Validation|
# =========================



# GRI 302 Sub-standard Requirements Mapping
GRI_302_REQUIREMENTS = {
    "302_1": [
        "energy_entries",
        "total_energy_mj",
        "renewable_energy_mj",
        "non_renewable_energy_mj",
        "base_year"
    ],
    "302_2": [
        "external_energy_mj",
        "base_year"
    ],
    "302_3": [
        "total_energy_mj",
        "employee_count",
        "intensity_denominator",
        "base_year"
    ],
    "302_4": [
        "energy_reduction_mj",
        "baseline_year",
        "base_year"
    ],
    "302_5": [
        "product_energy_reduction_mj",
        "base_year"
    ]
}

GRI_305_REQUIREMENTS = {
    "305_1": ["scope1_entries", "scope1_total_kg_co2e", "base_year"],
    "305_2": ["scope2_entries", "scope2_location_based_kg_co2e", "base_year"],
    "305_3": ["scope3_total_kg_co2e", "scope3_categories_included", "base_year"],
    "305_4": ["scope1_total_kg_co2e", "scope2_location_based_kg_co2e", "intensity_denominator", "base_year"],
    "305_5": ["ghg_reduction_kg_co2e", "baseline_year", "base_year"],
    "305_6": ["ods_kg_cfc11e", "base_year"],
    "305_7": ["nox_kg", "sox_kg", "base_year"]
}


GRI_401_REQUIREMENTS = {
    "401_1": [
        "total_new_hires",
        "total_turnover",
        "employee_count",
        "base_year"
    ],
    "401_2": [
        "benefits",
        "base_year"
    ],
    "401_3": [
        "parental_leave_by_gender",
        "base_year"
    ]
}

def has_required_fields(data: BaseModel, required_fields: List[str]) -> bool:
    """
    Check if all required fields are present (non-None) in the extracted data.
    
    Args:
        data: AIExtracted_GRI_302 instance
        required_fields: List of field names to check (e.g., ["total_energy_mj", "base_year"])
    
    Returns:
        bool: True if all required fields are non-None, False otherwise
    """
    for field in required_fields:
        if not hasattr(data, field) or getattr(data, field) is None:
            return False
    return True



def can_compute(substandard: str, data: BaseModel, requirements: Dict[str, List[str]]) -> bool:
    """
    Check if enough data is available to compute metrics for a specific GRI 302 sub-standard.
    
    Args:
        substandard: Sub-standard identifier (e.g., "302_1", "302_3")
        data: AIExtracted_GRI_302 instance
    
    Returns:
        bool: True if required fields for computation are available, False otherwise
    """
    if substandard not in requirements:
        return False
    return has_required_fields(data, requirements[substandard])