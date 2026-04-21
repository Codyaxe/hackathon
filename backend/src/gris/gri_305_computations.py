"""
GRI 305 (Emissions) Computation Engine

This module implements computation functions for each GRI 305 sub-standard:
- 305-1: Direct (Scope 1) GHG Emissions
- 305-2: Energy Indirect (Scope 2) GHG Emissions
- 305-3: Other Indirect (Scope 3) GHG Emissions
- 305-4: GHG Emissions Intensity
- 305-5: Reduction of GHG Emissions
- 305-6: Emissions of Ozone-Depleting Substances (ODS)
- 305-7: Nitrogen Oxides, Sulfur Oxides, and Other Air Emissions

All computation functions return structured results with:
- computed (bool): Whether the computation was successful
- value (Optional[float]): The computed value (if successful)
- unit (str): The unit of measurement
- metadata (dict): Additional context and information
- reason (Optional[str]): Explanation for failures (if unsuccessful)
"""

from typing import Dict, Optional, Any
from src.schemas.output_schemas import AIExtracted_GRI_305
from src.schemas.output_schemas import GRI_305_REQUIREMENTS
from src.schemas.output_schemas import can_compute


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================


def _calculate_year_span(
    baseline_year: Optional[str], reporting_year: Optional[str]
) -> Optional[int]:
    if baseline_year is None or reporting_year is None:
        return None
    try:
        return abs(int(reporting_year) - int(baseline_year))
    except (ValueError, TypeError):
        return None


def _get_missing_fields(data: AIExtracted_GRI_305, substandard: str) -> list[str]:
    return [
        f for f in GRI_305_REQUIREMENTS[substandard] if getattr(data, f, None) is None
    ]


def _not_computed(missing_fields: list[str], unit: str) -> Dict[str, Any]:
    return {
        "computed": False,
        "value": None,
        "unit": unit,
        "metadata": {},
        "reason": f"Missing required fields: {', '.join(missing_fields)}",
    }


# ============================================================================
# COMPUTATION FUNCTIONS FOR EACH GRI 305 SUB-STANDARD
# ============================================================================


def compute_305_1_scope1(data: AIExtracted_GRI_305) -> Dict[str, Any]:
    """
    Compute GRI 305-1: Direct (Scope 1) GHG Emissions.

    Aggregates all direct emission entries and returns total Scope 1 emissions
    broken down by biogenic and non-biogenic CO₂e.
    """
    if not can_compute("305_1", data, GRI_305_REQUIREMENTS):
        return _not_computed(_get_missing_fields(data, "305_1"), "kg CO2e")

    biogenic_kg = data.scope1_biogenic_kg_co2 or 0.0
    scope1_total = data.scope1_total_kg_co2e or 0.0
    non_biogenic = scope1_total - biogenic_kg

    ghg_gases = (
        list({gas for entry in data.scope1_entries for gas in entry.ghg_gases_included})
        if data.scope1_entries
        else []
    )

    return {
        "computed": True,
        "value": {
            "total_kg_co2e": scope1_total,
            "biogenic_kg_co2": biogenic_kg,
            "non_biogenic_kg_co2e": non_biogenic,
        },
        "unit": "kg CO2e",
        "metadata": {
            "base_year": data.base_year,
            "emission_entries_count": (
                len(data.scope1_entries) if data.scope1_entries else 0
            ),
            "ghg_gases_included": ghg_gases,
            "emission_factor_source": (
                data.emission_factor_metadata.source
                if data.emission_factor_metadata
                else None
            ),
        },
        "reason": None,
    }


def compute_305_2_scope2(data: AIExtracted_GRI_305) -> Dict[str, Any]:
    """
    Compute GRI 305-2: Energy Indirect (Scope 2) GHG Emissions.

    Returns location-based and market-based Scope 2 emissions if available.
    """
    if not can_compute("305_2", data, GRI_305_REQUIREMENTS):
        return _not_computed(_get_missing_fields(data, "305_2"), "kg CO2e")

    biogenic_kg = data.scope2_biogenic_kg_co2 or 0.0

    ghg_gases = (
        list({gas for entry in data.scope2_entries for gas in entry.ghg_gases_included})
        if data.scope2_entries
        else []
    )

    return {
        "computed": True,
        "value": {
            "location_based_kg_co2e": data.scope2_location_based_kg_co2e,
            "market_based_kg_co2e": data.scope2_market_based_kg_co2e,  # None if not reported
            "biogenic_kg_co2": biogenic_kg,
        },
        "unit": "kg CO2e",
        "metadata": {
            "base_year": data.base_year,
            "emission_entries_count": (
                len(data.scope2_entries) if data.scope2_entries else 0
            ),
            "ghg_gases_included": ghg_gases,
            "calculation_methodology": (
                data.emission_factor_metadata.calculation_methodology
                if data.emission_factor_metadata
                else None
            ),
            "emission_factor_source": (
                data.emission_factor_metadata.source
                if data.emission_factor_metadata
                else None
            ),
        },
        "reason": None,
    }


def compute_305_3_scope3(data: AIExtracted_GRI_305) -> Dict[str, Any]:
    """
    Compute GRI 305-3: Other Indirect (Scope 3) GHG Emissions.

    Returns total Scope 3 emissions and the categories included.
    """
    if not can_compute("305_3", data, GRI_305_REQUIREMENTS):
        return _not_computed(_get_missing_fields(data, "305_3"), "kg CO2e")

    biogenic_kg = data.scope3_biogenic_kg_co2 or 0.0

    return {
        "computed": True,
        "value": {
            "total_kg_co2e": data.scope3_total_kg_co2e,
            "biogenic_kg_co2": biogenic_kg,
        },
        "unit": "kg CO2e",
        "metadata": {
            "base_year": data.base_year,
            "categories_included": data.scope3_categories_included,
            "emission_factor_source": (
                data.emission_factor_metadata.source
                if data.emission_factor_metadata
                else None
            ),
        },
        "reason": None,
    }


def compute_305_4_intensity(data: AIExtracted_GRI_305) -> Dict[str, Any]:
    """
    Compute GRI 305-4: GHG Emissions Intensity.

    Calculates intensity ratio using total Scope 1 + Scope 2 emissions
    divided by employee count or revenue. Prioritizes employee_count.
    """
    if not can_compute("305_4", data, GRI_305_REQUIREMENTS):
        return _not_computed(_get_missing_fields(data, "305_4"), "kg CO2e")

    # Total emissions = Scope 1 + Scope 2 (location-based)
    total_emissions = (data.scope1_total_kg_co2e or 0.0) + (
        data.scope2_location_based_kg_co2e or 0.0
    )

    # Determine denominator — prefer employee count
    if data.employee_count is not None and data.employee_count > 0:
        denominator_type = "per_employee"
        denominator_value = data.employee_count
        intensity_value = total_emissions / data.employee_count
        unit = "kg CO2e per employee"

    elif data.revenue is not None and data.revenue > 0:
        denominator_type = "per_revenue_unit"
        denominator_value = data.revenue
        intensity_value = total_emissions / data.revenue
        unit = "kg CO2e per currency unit"

    else:
        missing = []
        if data.employee_count is None:
            missing.append("employee_count")
        if data.revenue is None:
            missing.append("revenue")
        return {
            "computed": False,
            "value": None,
            "unit": "kg CO2e",
            "metadata": {},
            "reason": f"Missing denominator fields: {', '.join(missing)}",
        }

    return {
        "computed": True,
        "value": intensity_value,
        "unit": unit,
        "metadata": {
            "base_year": data.base_year,
            "denominator_type": denominator_type,
            "denominator_value": denominator_value,
            "total_emissions_kg_co2e": total_emissions,
            "scopes_included": data.intensity_scopes_included,
            "specified_denominator": data.intensity_denominator,
        },
        "reason": None,
    }


def compute_305_5_reduction(data: AIExtracted_GRI_305) -> Dict[str, Any]:
    """
    Compute GRI 305-5: Reduction of GHG Emissions.

    Returns absolute reduction vs baseline and percentage if current
    emissions are available to compare against.
    """
    if not can_compute("305_5", data, GRI_305_REQUIREMENTS):
        return _not_computed(_get_missing_fields(data, "305_5"), "kg CO2e")

    reduction_percentage = None
    baseline_emissions = None

    # Only compute percentage if we have current emissions to compare against
    current_emissions = (data.scope1_total_kg_co2e or 0.0) + (
        data.scope2_location_based_kg_co2e or 0.0
    )
    reduction_kg = data.ghg_reduction_kg_co2e or 0.0
    if current_emissions > 0:
        baseline_emissions = current_emissions + reduction_kg
        reduction_percentage = (
            (reduction_kg / baseline_emissions) * 100 if baseline_emissions > 0 else 0.0
        )

    return {
        "computed": True,
        "value": {
            "reduction_kg_co2e": reduction_kg,
            "reduction_percentage": reduction_percentage,  # None if current emissions unavailable
            "baseline_emissions_kg_co2e": baseline_emissions,  # None if not computable
            "current_emissions_kg_co2e": (
                current_emissions if current_emissions > 0 else None
            ),
        },
        "unit": "kg CO2e",
        "metadata": {
            "baseline_year": data.baseline_year,
            "reporting_year": data.base_year,
            "years_span": _calculate_year_span(data.baseline_year, data.base_year),
            "scopes_included": data.reduction_scopes_included,
        },
        "reason": None,
    }


def compute_305_6_ods(data: AIExtracted_GRI_305) -> Dict[str, Any]:
    """
    Compute GRI 305-6: Emissions of Ozone-Depleting Substances (ODS).

    Returns total ODS in metric tons CFC-11 equivalent and lists substances.
    """
    if not can_compute("305_6", data, GRI_305_REQUIREMENTS):
        return _not_computed(_get_missing_fields(data, "305_6"), "metric tons CFC-11e")

    return {
        "computed": True,
        "value": data.ods_kg_cfc11e,
        "unit": "metric tons CFC-11e",
        "metadata": {
            "base_year": data.base_year,
            "substances_reported": data.ods_substances,
        },
        "reason": None,
    }


def compute_305_7_air_emissions(data: AIExtracted_GRI_305) -> Dict[str, Any]:
    """
    Compute GRI 305-7: Nitrogen Oxides, Sulfur Oxides, and Other Air Emissions.

    Returns all available air pollutant values in kilograms.
    """
    if not can_compute("305_7", data, GRI_305_REQUIREMENTS):
        return _not_computed(_get_missing_fields(data, "305_7"), "kg")

    return {
        "computed": True,
        "value": {
            "nox_kg": data.nox_kg,
            "sox_kg": data.sox_kg,
            "voc_kg": data.voc_kg,  # None if not reported
            "pm_kg": data.pm_kg,  # None if not reported
        },
        "unit": "kg",
        "metadata": {
            "base_year": data.base_year,
        },
        "reason": None,
    }


# ============================================================================
# GRI 305 COMPUTATION FUNCTION REGISTRY
# ============================================================================

GRI_305_FUNCTIONS = {
    "305_1": compute_305_1_scope1,
    "305_2": compute_305_2_scope2,
    "305_3": compute_305_3_scope3,
    "305_4": compute_305_4_intensity,
    "305_5": compute_305_5_reduction,
    "305_6": compute_305_6_ods,
    "305_7": compute_305_7_air_emissions,
}
