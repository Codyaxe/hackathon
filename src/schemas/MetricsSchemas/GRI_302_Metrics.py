from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

class EnergyEntry(BaseModel):

    energy_type: str = Field(
        description=(
            "Type of energy source. Use lowercase standard names: "
            "'electricity', 'diesel', 'LPG', 'solar', 'natural_gas', 'coal', 'wind'. "
            "Never merge two sources into one entry."
        )
    )

    value: float = Field(
        ge=0,
        description="Numeric quantity of energy consumed as stated in the source. Do not convert this value."
    )

    unit: str = Field(
        description="Unit of the value as stated. E.g. 'kWh', 'liters', 'm3', 'kg'. Must match value before conversion."
    )

    converted_mj: float = Field(
        ge=0,
        description=(
            "Value converted to Megajoules (MJ) using standard factors: "
            "electricity 3.6 MJ/kWh, diesel 36.54 MJ/liter, LPG 25.3 MJ/liter, natural_gas 38.3 MJ/m3. "
            "Always compute this — never leave at 0 unless value is genuinely zero."
        )
    )

    is_renewable: bool = Field(
        default=False,
        description="True only for solar, wind, hydro, or biomass. False for electricity from grid, diesel, LPG, natural_gas, coal."
    )

    source: Optional[str] = Field(
        default=None,
        description="Equipment or activity this energy was consumed by. E.g. 'electric oven', 'backup diesel generator', 'solar rooftop panels'."
    )

    confidence: float = Field(
        default=0.8,
        ge=0,
        le=1,
        description=(
            "How explicitly the value was stated. "
            "1.0 = exact figure from a document. "
            "0.7-0.9 = estimated or approximate ('around 150 liters'). "
            "0.5-0.6 = vague or inferred ('a few tanks a week'). "
            "Below 0.5 = handwritten, unclear, or conflicting records."
        )
    )


class ConversionFactors(BaseModel):


    electricity_kwh_to_mj: float = 3.6
    diesel_liter_to_mj: float = 36.54
    source: str = "IPCC Default Emission Factors 2006"








class Omission302(BaseModel):
    field_name: Literal[
        "energy_entries",
        "total_energy_mj",
        "renewable_energy_mj",
        "non_renewable_energy_mj",
        "external_energy_mj",
        "employee_count",
        "revenue",
        "intensity_denominator",
        "energy_reduction_mj",
        "baseline_year",
        "product_energy_reduction_mj",
        "conversion_factors",
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
