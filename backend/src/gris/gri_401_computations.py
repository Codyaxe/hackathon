"""
GRI 401 (Employment) Computation Engine

This module implements computation functions for each GRI 401 sub-standard:
- 401-1: New Employee Hires and Employee Turnover
- 401-2: Benefits Provided to Full-Time Employees
- 401-3: Parental Leave (Optional)

All computation functions return structured results with:
- computed (bool): Whether the computation was successful
- value (Optional[float]): The computed value (if successful)
- unit (str): The unit of measurement
- metadata (dict): Additional context and information
- reason (Optional[str]): Explanation for failures (if unsuccessful)
"""

# FILE: gri_401_computations.py

from typing import Dict, Optional, Any
from src.schemas.output_schemas import AIExtracted_GRI_401
from src.schemas.output_schemas import GRI_401_REQUIREMENTS
from src.schemas.output_schemas import can_compute


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================


def _get_missing_fields(data: AIExtracted_GRI_401, substandard: str) -> list[str]:
    return [
        f for f in GRI_401_REQUIREMENTS[substandard] if getattr(data, f, None) is None
    ]


def _not_computed(missing_fields: list[str], unit: str) -> Dict[str, Any]:
    return {
        "computed": False,
        "value": None,
        "unit": unit,
        "metadata": {},
        "reason": f"Missing required fields: {', '.join(missing_fields)}",
    }


def _compute_rate(
    numerator: Optional[int], denominator: Optional[int]
) -> Optional[float]:
    """Compute a percentage rate safely. Returns None if either value is missing or denominator is 0."""
    if numerator is None or denominator is None or denominator == 0:
        return None
    return round((numerator / denominator) * 100, 2)


# ============================================================================
# COMPUTATION FUNCTIONS FOR EACH GRI 401 SUB-STANDARD
# ============================================================================


def compute_401_1_hires_and_turnover(data: AIExtracted_GRI_401) -> Dict[str, Any]:
    """
    Compute GRI 401-1: New Employee Hires and Employee Turnover.

    Extracts and validates hire and turnover counts and rates,
    with breakdowns by gender, age group, and region where available.

    Args:
        data: AIExtracted_GRI_401 instance with hire and turnover data

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
        >>> data = AIExtracted_GRI_401(
        ...     total_new_hires=2,
        ...     total_turnover=1,
        ...     employee_count=12,
        ...     base_year="2025"
        ... )
        >>> result = compute_401_1_hires_and_turnover(data)
        >>> result["computed"]
        True
        >>> result["value"]["new_hire_rate"]
        16.67
    """
    if not can_compute("401_1", data, GRI_401_REQUIREMENTS):
        return _not_computed(_get_missing_fields(data, "401_1"), "headcount")

    # Recompute rates from raw counts if available — do not trust AI-computed rates blindly
    new_hire_rate = _compute_rate(data.total_new_hires, data.employee_count)
    turnover_rate = _compute_rate(data.total_turnover, data.employee_count)

    return {
        "computed": True,
        "value": {
            "new_hires": {
                "total": data.total_new_hires,
                "rate": new_hire_rate,
                "by_gender": (
                    data.new_hires_by_gender.model_dump()
                    if data.new_hires_by_gender
                    else None
                ),
                "by_age_group": (
                    data.new_hires_by_age_group.model_dump()
                    if data.new_hires_by_age_group
                    else None
                ),
                "by_region": (
                    [r.model_dump() for r in data.new_hires_by_region]
                    if data.new_hires_by_region
                    else None
                ),
            },
            "turnover": {
                "total": data.total_turnover,
                "rate": turnover_rate,
                "by_gender": (
                    data.turnover_by_gender.model_dump()
                    if data.turnover_by_gender
                    else None
                ),
                "by_age_group": (
                    data.turnover_by_age_group.model_dump()
                    if data.turnover_by_age_group
                    else None
                ),
                "by_region": (
                    [r.model_dump() for r in data.turnover_by_region]
                    if data.turnover_by_region
                    else None
                ),
            },
        },
        "unit": "headcount",
        "metadata": {
            "base_year": data.base_year,
            "employee_count": data.employee_count,
            "has_gender_breakdown": data.new_hires_by_gender is not None
            or data.turnover_by_gender is not None,
            "has_age_breakdown": data.new_hires_by_age_group is not None
            or data.turnover_by_age_group is not None,
            "has_region_breakdown": data.new_hires_by_region is not None
            or data.turnover_by_region is not None,
        },
        "reason": None,
    }


def compute_401_2_benefits(data: AIExtracted_GRI_401) -> Dict[str, Any]:
    """
    Compute GRI 401-2: Benefits Provided to Full-Time Employees.

    Extracts the list of benefits and identifies which are exclusive
    to full-time employees vs available to all.

    Args:
        data: AIExtracted_GRI_401 instance with benefits data

    Returns:
        Dict with structure:
        {
            "computed": bool,
            "value": {...} or None,
            "unit": str,
            "metadata": {...},
            "reason": Optional[str]
        }
    """
    if not can_compute("401_2", data, GRI_401_REQUIREMENTS):
        return _not_computed(_get_missing_fields(data, "401_2"), "benefits")

    benefits = data.benefits or []

    full_time_only = [
        b.model_dump() for b in benefits if b.full_time and not b.part_time_or_temporary
    ]
    shared_benefits = [
        b.model_dump() for b in benefits if b.full_time and b.part_time_or_temporary
    ]
    not_provided = [b.model_dump() for b in benefits if not b.full_time]

    return {
        "computed": True,
        "value": {
            "full_time_only": full_time_only,
            "shared_with_part_time": shared_benefits,
            "not_provided": not_provided,
            "total_benefits_tracked": len(benefits),
        },
        "unit": "benefits",
        "metadata": {
            "base_year": data.base_year,
            "significant_location": data.significant_location,
        },
        "reason": None,
    }


def compute_401_3_parental_leave(data: AIExtracted_GRI_401) -> Dict[str, Any]:
    """
    Compute GRI 401-3: Parental Leave.

    Extracts parental leave uptake, return-to-work, and 12-month
    retention rates broken down by gender.

    Args:
        data: AIExtracted_GRI_401 instance with parental leave data

    Returns:
        Dict with structure:
        {
            "computed": bool,
            "value": {...} or None,
            "unit": str,
            "metadata": {...},
            "reason": Optional[str]
        }
    """
    if not can_compute("401_3", data, GRI_401_REQUIREMENTS):
        return _not_computed(_get_missing_fields(data, "401_3"), "headcount")

    # Compute return-to-work and retention rates per gender from raw counts
    computed_rates = []
    parental_leave_entries = data.parental_leave_by_gender or []
    for entry in parental_leave_entries:
        return_rate = _compute_rate(entry.returned_to_work, entry.took_leave)
        retention_rate = _compute_rate(
            entry.still_employed_after_12_months, entry.returned_to_work
        )
        computed_rates.append(
            {
                "gender": entry.gender,
                "entitled": entry.entitled,
                "took_leave": entry.took_leave,
                "returned_to_work": entry.returned_to_work,
                "still_employed_after_12_months": entry.still_employed_after_12_months,
                "return_to_work_rate": return_rate,
                "retention_rate_12_months": retention_rate,
            }
        )

    return {
        "computed": True,
        "value": {"by_gender": computed_rates},
        "unit": "headcount",
        "metadata": {
            "base_year": data.base_year,
            "genders_reported": [e["gender"] for e in computed_rates],
        },
        "reason": None,
    }


# ============================================================================
# GRI 401 COMPUTATION FUNCTION REGISTRY
# ============================================================================

GRI_401_FUNCTIONS = {
    "401_1": compute_401_1_hires_and_turnover,
    "401_2": compute_401_2_benefits,
    "401_3": compute_401_3_parental_leave,
}
