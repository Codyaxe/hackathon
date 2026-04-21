from typing import Any, Callable, Dict, List

from pydantic import BaseModel

# ============================================================================
# GRI 302 ENGINE
# ============================================================================


class GRIEngine:
    """
    Generic computation engine for any GRI standard.

    Accepts a functions registry and requirements map at instantiation,
    making it reusable across GRI 302, 305, 401, and any future standards.

    Example:
        >>> from src.gris.gri_302.computations import GRI_302_FUNCTIONS
        >>> from src.gris.gri_302.requirements import GRI_302_REQUIREMENTS
        >>> engine = GRIEngine(GRI_302_FUNCTIONS, GRI_302_REQUIREMENTS)
        >>> results = engine.run(data)
        >>> results["302_1"]["computed"]
        True
    """

    def __init__(
        self, functions: Dict[str, Callable], requirements: Dict[str, List[str]]
    ):
        """
        Initialize the GRIEngine.

        Args:
            functions: Registry mapping substandard keys to compute functions.
                       E.g. {"302_1": compute_302_1_energy_totals, ...}
            requirements: Mapping of substandard keys to required field names.
                          E.g. {"302_1": ["total_energy_mj", "base_year"], ...}
        """
        self.functions = functions
        self.requirements = requirements

    def run(self, data: BaseModel) -> Dict[str, Dict[str, Any]]:
        """
        Execute all computations on the provided extracted data.

        This method:
        1. Loops through all registered substandard computation functions
        2. Executes each function against the data
        3. Returns results for all substandards plus a summary

        Args:
            data: Any GRI extracted data instance (AIExtracted_GRI_302,
                  AIExtracted_GRI_305, etc.)

        Returns:
            Dict with results for each substandard plus a summary:
            {
                "<substandard>": {
                    "computed": bool,
                    "value": ...,
                    "unit": str,
                    "metadata": {...},
                    "reason": Optional[str]
                },
                ...
                "summary": {
                    "computed_count": int,
                    "total_count": int,
                    "availability": {...},
                    "base_year": Optional[str],
                    "has_omitted_fields": bool,
                    "omitted_fields": Optional[list]
                }
            }

        Example:
            >>> results = engine.run(data)
            >>> if results["302_1"]["computed"]:
            ...     print(f"Total energy: {results['302_1']['value']['total_energy_mj']} MJ")
        """
        from src.schemas.output_schemas import can_compute

        results = {}
        availability = {}
        computed_count = 0

        for substandard, compute_func in self.functions.items():
            is_computable = can_compute(substandard, data, self.requirements)
            availability[substandard] = is_computable

            result = compute_func(data)
            results[substandard] = result

            if result["computed"]:
                computed_count += 1

        omitted_raw = getattr(data, "omitted_fields", None)
        omitted = omitted_raw if omitted_raw else None
        base_year = getattr(data, "base_year", None)

        results["summary"] = {
            "computed_count": computed_count,
            "total_count": len(self.functions),
            "availability": availability,
            "base_year": base_year,
            "has_omitted_fields": bool(omitted),
            "omitted_fields": omitted,
        }

        return results
