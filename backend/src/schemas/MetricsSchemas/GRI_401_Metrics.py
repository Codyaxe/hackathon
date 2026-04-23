from typing import Literal, Optional
from pydantic import BaseModel, Field


# FILE: GRI_401_Metrics.py


class BreakdownByGender(BaseModel):
    male: Optional[int] = Field(
        default=None,
        ge=0,
        description="Count for male employees. Set to null if not reported."
    )
    female: Optional[int] = Field(
        default=None,
        ge=0,
        description="Count for female employees. Set to null if not reported."
    )
    other: Optional[int] = Field(
        default=None,
        ge=0,
        description="Count for non-binary or other gender identities. Set to null if not reported."
    )


class BreakdownByAgeGroup(BaseModel):
    under_30: Optional[int] = Field(
        default=None,
        ge=0,
        description="Count for employees under 30 years old. Set to null if not reported."
    )
    between_30_and_50: Optional[int] = Field(
        default=None,
        ge=0,
        description="Count for employees aged 30 to 50. Set to null if not reported."
    )
    over_50: Optional[int] = Field(
        default=None,
        ge=0,
        description="Count for employees over 50 years old. Set to null if not reported."
    )


class BreakdownByRegion(BaseModel):
    region: str = Field(
        description="Name of the region or location. E.g. 'Quezon City, NCR', 'Cebu', 'Davao'."
    )
    count: int = Field(
        ge=0,
        description="Number of employees in this region."
    )


class BenefitEntry(BaseModel):
    benefit_name: str = Field(
        description=(
            "Name of the benefit. Use standard names: "
            "'life_insurance', 'healthcare', 'disability_coverage', "
            "'parental_leave', 'retirement', 'stock_ownership', '13th_month_pay', "
            "'philhealth', 'sss', 'pagibig'. Use lowercase with underscores."
        )
    )
    full_time: bool = Field(
        description="True if this benefit is provided to full-time employees."
    )
    part_time_or_temporary: bool = Field(
        description="True if this benefit is also provided to part-time or temporary employees."
    )



# Add to GRI_401_Metrics.py
class GenderRate(BaseModel):
    gender: str = Field(
        description="Gender category. Use 'male', 'female', or 'other'."
    )
    rate: Optional[float] = Field(
        default=None,
        ge=0,
        le=100,
        description="Rate as a percentage (0-100). Set to null if not computable."
    )


class ParentalLeaveByGender(BaseModel):
    gender: str = Field(
        description="Gender category. Use 'male', 'female', or 'other'."
    )
    entitled: Optional[int] = Field(
        default=None,
        ge=0,
        description="Number of employees entitled to parental leave. Set to null if not reported."
    )
    took_leave: Optional[int] = Field(
        default=None,
        ge=0,
        description="Number of employees who actually took parental leave. Set to null if not reported."
    )
    returned_to_work: Optional[int] = Field(
        default=None,
        ge=0,
        description="Number who returned to work after parental leave ended. Set to null if not reported."
    )
    still_employed_after_12_months: Optional[int] = Field(
        default=None,
        ge=0,
        description="Number still employed 12 months after returning from parental leave. Set to null if not reported."
    )


class Omission401(BaseModel):
    field_name: Literal[
        "total_new_hires",
        "new_hire_rate",
        "new_hires_by_gender",
        "new_hires_by_age_group",
        "new_hires_by_region",
        "total_turnover",
        "turnover_rate",
        "turnover_by_gender",
        "turnover_by_age_group",
        "turnover_by_region",
        "benefits",
        "significant_location",
        "parental_leave_by_gender",
        "return_to_work_rate_by_gender",
        "retention_rate_by_gender",
        "base_year"
    ] = Field(
        description=(
            "The exact field name that could not be populated. "
            "Must be one of the defined GRI 401 fields. "
            "Do not invent field names outside this list."
        )
    )
    reason: str = Field(
        description=(
            "Specific reason why this field is absent. "
            "Reference the source material directly — e.g. 'HR records do not break down hires by age group', "
            "'no parental leave was taken during the reporting period'. "
            "Do not use generic reasons like 'not found' or 'missing'."
        )
    )