"""
GRI 302 (Energy) Computation Engine

This module implements computation functions for each GRI 302 sub-standard:
- 302-1: Energy Consumption Within the Organization
- 302-2: Energy Consumption Outside of the Organization
- 302-3: Energy Intensity
- 302-4: Reduction of Energy Consumption
- 302-5: Reductions in Energy Requirements of Sold Products and Services

All computation functions return structured results with:
- computed (bool): Whether the computation was successful
- value (Optional[float]): The computed value (if successful)
- unit (str): The unit of measurement
- metadata (dict): Additional context and information
- reason (Optional[str]): Explanation for failures (if unsuccessful)
"""

from typing import Dict, Optional, Any
from src.schemas.output_schemas import AIExtracted_GRI_302
from src.schemas.output_schemas import GRI_302_REQUIREMENTS
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


def _get_missing_fields(data: AIExtracted_GRI_302, substandard: str) -> list[str]:
    return [
        f for f in GRI_302_REQUIREMENTS[substandard] if getattr(data, f, None) is None
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
# COMPUTATION FUNCTIONS FOR EACH GRI 302 SUB-STANDARD
# ============================================================================


def compute_302_1_energy_totals(data: AIExtracted_GRI_302) -> Dict[str, Any]:
    """
    Compute GRI 302-1: Energy Consumption Within the Organization.

    Calculates total energy consumption broken down by renewable
    and non-renewable sources.

    Args:
        data: AIExtracted_GRI_302 instance with energy data

    Returns:
        Dict with structure:
        {
            "computed": bool,
            "value": {...} or None,
            "unit": str,
            "metadata": {...},
            "reason": Optional[str]
        }

    Example:
        >>> data = AIExtracted_GRI_302(
        ...     total_energy_mj=1000.0,
        ...     renewable_energy_mj=300.0,
        ...     non_renewable_energy_mj=700.0,
        ...     base_year="2024"
        ... )
        >>> result = compute_302_1_energy_totals(data)
        >>> result["computed"]
        True
        >>> result["value"]["total_energy_mj"]
        1000.0
    """
    if not can_compute("302_1", data, GRI_302_REQUIREMENTS):
        return _not_computed(_get_missing_fields(data, "302_1"), "MJ")

    renewable_pct = 0.0
    total_energy_mj = data.total_energy_mj or 0.0
    renewable_energy_mj = data.renewable_energy_mj or 0.0
    if total_energy_mj > 0:
        renewable_pct = (renewable_energy_mj / total_energy_mj) * 100

    return {
        "computed": True,
        "value": {
            "total_energy_mj": data.total_energy_mj,
            "renewable_energy_mj": data.renewable_energy_mj,
            "non_renewable_energy_mj": data.non_renewable_energy_mj,
            "renewable_percentage": renewable_pct,
        },
        "unit": "MJ",
        "metadata": {
            "base_year": data.base_year,
            "energy_entries_count": (
                len(data.energy_entries) if data.energy_entries else 0
            ),
            "conversion_factors_used": data.conversion_factors is not None,
        },
        "reason": None,
    }


def compute_302_2_external_energy(data: AIExtracted_GRI_302) -> Dict[str, Any]:
    """
    Compute GRI 302-2: Energy Consumption Outside of the Organization.

    Extracts external energy consumption from purchased electricity,
    steam, heating, or cooling.

    Args:
        data: AIExtracted_GRI_302 instance with external energy data

    Returns:
        Dict with structure:
        {
            "computed": bool,
            "value": float or None,
            "unit": str,
            "metadata": {...},
            "reason": Optional[str]
        }
    """
    if not can_compute("302_2", data, GRI_302_REQUIREMENTS):
        return _not_computed(_get_missing_fields(data, "302_2"), "MJ")

    return {
        "computed": True,
        "value": data.external_energy_mj,
        "unit": "MJ",
        "metadata": {
            "base_year": data.base_year,
            "source": "Purchased electricity, steam, heating, or cooling",
        },
        "reason": None,
    }


def compute_302_3_intensity(data: AIExtracted_GRI_302) -> Dict[str, Any]:
    """
    Compute GRI 302-3: Energy Intensity.

    Calculates energy intensity ratio using either employee count
    or revenue as the denominator. Prioritizes employee_count if available.

    Args:
        data: AIExtracted_GRI_302 instance with intensity data

    Returns:
        Dict with structure:
        {
            "computed": bool,
            "value": float or None,
            "unit": str,
            "metadata": {...},
            "reason": Optional[str]
        }

    Example:
        >>> data = AIExtracted_GRI_302(
        ...     total_energy_mj=1000.0,
        ...     employee_count=100,
        ...     intensity_denominator="per_employee",
        ...     base_year="2024"
        ... )
        >>> result = compute_302_3_intensity(data)
        >>> result["value"]
        10.0  # MJ per employee
    """
    if data.total_energy_mj is None:
        return _not_computed(["total_energy_mj"], "MJ")

    if data.employee_count is not None and data.employee_count > 0:
        denominator_type = "per_employee"
        denominator_value = data.employee_count
        intensity_value = data.total_energy_mj / data.employee_count
        unit = "MJ per employee"

    elif data.revenue is not None and data.revenue > 0:
        denominator_type = "per_revenue_unit"
        denominator_value = data.revenue
        intensity_value = data.total_energy_mj / data.revenue
        unit = "MJ per currency unit"

    else:
        missing = []
        if data.employee_count is None:
            missing.append("employee_count")
        if data.revenue is None:
            missing.append("revenue")
        return _not_computed(missing, "MJ")

    return {
        "computed": True,
        "value": intensity_value,
        "unit": unit,
        "metadata": {
            "base_year": data.base_year,
            "denominator_type": denominator_type,
            "denominator_value": denominator_value,
            "total_energy_mj": data.total_energy_mj,
            "specified_denominator": data.intensity_denominator,
        },
        "reason": None,
    }


def compute_302_4_reduction(data: AIExtracted_GRI_302) -> Dict[str, Any]:
    """
    Compute GRI 302-4: Reduction of Energy Consumption.

    Calculates energy reduction metrics including absolute reduction
    and percentage reduction from baseline.

    Args:
        data: AIExtracted_GRI_302 instance with reduction data

    Returns:
        Dict with structure:
        {
            "computed": bool,
            "value": {...} or None,
            "unit": str,
            "metadata": {...},
            "reason": Optional[str]
        }

    Example:
        >>> data = AIExtracted_GRI_302(
        ...     energy_reduction_mj=100.0,
        ...     total_energy_mj=1000.0,
        ...     baseline_year="2020",
        ...     base_year="2024"
        ... )
        >>> result = compute_302_4_reduction(data)
        >>> result["value"]["reduction_percentage"]
        9.09...  # 100 / (1000 + 100) * 100
    """
    if not can_compute("302_4", data, GRI_302_REQUIREMENTS):
        return _not_computed(_get_missing_fields(data, "302_4"), "MJ")

    reduction_percentage = None
    baseline_energy = None

    reduction_mj = data.energy_reduction_mj or 0.0
    if data.total_energy_mj is not None and data.total_energy_mj >= 0:
        baseline_energy = data.total_energy_mj + reduction_mj
        reduction_percentage = (
            (reduction_mj / baseline_energy) * 100 if baseline_energy > 0 else 0.0
        )

    return {
        "computed": True,
        "value": {
            "reduction_mj": reduction_mj,
            "reduction_percentage": reduction_percentage,
            "baseline_energy_mj": baseline_energy,
            "current_energy_mj": data.total_energy_mj,
        },
        "unit": "MJ",
        "metadata": {
            "baseline_year": data.baseline_year,
            "reporting_year": data.base_year,
            "years_span": _calculate_year_span(data.baseline_year, data.base_year),
        },
        "reason": None,
    }


def compute_302_5_product_reduction(data: AIExtracted_GRI_302) -> Dict[str, Any]:
    """
    Compute GRI 302-5: Reductions in Energy Requirements of Sold Products and Services.

    Extracts product-level energy reduction metrics.

    Args:
        data: AIExtracted_GRI_302 instance with product reduction data

    Returns:
        Dict with structure:
        {
            "computed": bool,
            "value": float or None,
            "unit": str,
            "metadata": {...},
            "reason": Optional[str]
        }
    """
    if not can_compute("302_5", data, GRI_302_REQUIREMENTS):
        return _not_computed(_get_missing_fields(data, "302_5"), "MJ")

    return {
        "computed": True,
        "value": data.product_energy_reduction_mj,
        "unit": "MJ",
        "metadata": {
            "base_year": data.base_year,
            "category": "Sold products and services",
        },
        "reason": None,
    }


# ============================================================================
# GRI 302 COMPUTATION FUNCTION REGISTRY
# ============================================================================

GRI_302_FUNCTIONS = {
    "302_1": compute_302_1_energy_totals,
    "302_2": compute_302_2_external_energy,
    "302_3": compute_302_3_intensity,
    "302_4": compute_302_4_reduction,
    "302_5": compute_302_5_product_reduction,
}
