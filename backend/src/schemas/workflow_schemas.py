from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class OnboardingQuizContext(BaseModel):
    company_id: str = Field(min_length=1)
    company_name: str = Field(min_length=1)
    industry: str = Field(min_length=1)
    employee_count: int = Field(ge=1)
    annual_revenue: float | None = Field(default=None, ge=0)
    primary_country: str | None = None
    location: str | None = None


class WorkflowQuestion(BaseModel):
    question_id: str
    prompt: str
    field_name: str
    input_type: Literal["single_choice", "multi_choice", "boolean", "number", "text"]
    options: list[str] = Field(default_factory=list)
    required: bool = True


class QuestionAnswer(BaseModel):
    question_id: str
    value: Any


class FocusArea(BaseModel):
    area: Literal[
        "energy",
        "emissions",
        "waste",
        "workforce",
        "governance",
        "data_foundation",
        "supply_chain",
    ]
    priority: Literal["high", "medium", "low"]
    reason: str


class OnboardingQuizResponse(BaseModel):
    context: OnboardingQuizContext
    questions: list[WorkflowQuestion]


class OnboardingRecommendationResponse(BaseModel):
    company_id: str
    focus_areas: list[FocusArea]
    recommendation_summary: str
    next_steps: list[str]


class OnboardingQuizSubmission(BaseModel):
    context: OnboardingQuizContext
    answers: list[QuestionAnswer] = Field(default_factory=list)


class ESGPlanRequest(BaseModel):
    company_id: str
    planning_horizon_days: int = Field(default=90, ge=30, le=365)
    preferred_focus_areas: list[str] = Field(default_factory=list)


class ESGPlanAction(BaseModel):
    title: str
    why_it_matters: str
    effort: Literal["low", "medium", "high"]
    timeline_weeks: int = Field(ge=1, le=26)
    owner: str
    success_metric: str


class ESGPlanResponse(BaseModel):
    company_id: str
    generated_at: datetime
    one_page_summary: str
    priority_themes: list[str]
    actions: list[ESGPlanAction]
    monthly_check_in_questions: list[str]
    kpis: list[str] = Field(default_factory=list)
    ready_for_pdf: bool = False


class UploadedFileRecord(BaseModel):
    file_id: str
    filename: str
    media_type: str
    size_bytes: int = Field(ge=0)
    uploaded_at: datetime
    disclosure_tag: str | None = None


class EvidenceFileRecord(BaseModel):
    file_id: str
    filename: str
    media_type: str
    size_bytes: int = Field(ge=0)
    uploaded_at: datetime
    disclosure_tag: str | None = None


class EvidenceListResponse(BaseModel):
    company_id: str
    evidence_files: list[EvidenceFileRecord]


class ExtractedMetric(BaseModel):
    metric_name: str
    value: str
    unit: str | None = None
    category: str
    confidence: float = Field(default=0.7, ge=0, le=1)
    evidence: str | None = None


class AIFileExtractionResult(BaseModel):
    model_config = ConfigDict(extra="ignore")

    summary: str = "Could not confidently extract ESG metrics from the uploaded files."
    metrics: list[ExtractedMetric] = Field(default_factory=list)
    follow_up_questions: list[str] = Field(default_factory=list)


class FixedExtractionMetrics(BaseModel):
    electricity_kwh: float | None = Field(default=None, ge=0)
    diesel_liters: float | None = Field(default=None, ge=0)
    waste_kg: float | None = Field(default=None, ge=0)
    headcount: int | None = Field(default=None, ge=0)
    new_hires: int | None = Field(default=None, ge=0)
    turnover_count: int | None = Field(default=None, ge=0)
    missing_fields: list[str] = Field(default_factory=list)


class FileExtractionResponse(BaseModel):
    company_id: str
    files: list[UploadedFileRecord]
    extracted_metrics: list[ExtractedMetric]
    ai_summary: str
    follow_up_questions: list[str]
    fixed_extraction: FixedExtractionMetrics | None = None


class ResponseLibraryEntry(BaseModel):
    entry_id: str
    entry_type: Literal["onboarding", "plan", "upload_extraction", "monthly_update"]
    created_at: datetime
    payload: dict[str, Any]


class ResponseLibraryResponse(BaseModel):
    company_id: str
    entries: list[ResponseLibraryEntry]


class ProgressStep(BaseModel):
    step_id: str
    title: str
    completed: bool
    score: int = Field(ge=0, le=100)
    improvement_tip: str


class DashboardKPI(BaseModel):
    name: str
    value: float | int | str
    unit: str | None = None
    rating: Literal["Good", "Better", "Best"]


class OmissionReason(BaseModel):
    disclosure: str
    reason: str


class ProgressTrackerResponse(BaseModel):
    company_id: str
    completion_percentage: float = Field(ge=0, le=100)
    maturity_stage: Literal[
        "getting_started",
        "building_baseline",
        "improving",
        "advanced",
    ]
    steps: list[ProgressStep]
    next_best_actions: list[str]
    esg_score: float = Field(default=0, ge=0, le=100)
    compliance_status: Literal["On Track", "Needs Attention"] = "Needs Attention"
    kpis: list[DashboardKPI] = Field(default_factory=list)
    quick_wins_with_savings: list[QuickWinItem] = Field(default_factory=list)


class QuickWinItem(BaseModel):
    title: str
    impact_area: str
    effort: Literal["low", "medium"]
    expected_benefit: str
    why_recommended: str
    first_step: str
    estimated_cost_savings_php: float | None = Field(default=None, ge=0)


class QuickWinsResponse(BaseModel):
    company_id: str
    generated_at: datetime
    quick_wins: list[QuickWinItem]


class MonthlyUpdateQuestion(BaseModel):
    question_id: str
    prompt: str
    field_name: str
    input_type: Literal["number", "text", "boolean", "single_choice"]
    options: list[str] = Field(default_factory=list)
    required: bool = True


class MonthlyUpdateQuestionsResponse(BaseModel):
    company_id: str
    month: str
    context_message: str
    questions: list[MonthlyUpdateQuestion]


class MonthlyUpdateSubmission(BaseModel):
    company_id: str
    month: str = Field(description="Expected format YYYY-MM")
    changes: dict[str, Any] = Field(default_factory=dict)
    notes: str | None = None


class MonthlyUpdateResponse(BaseModel):
    company_id: str
    month: str
    change_summary: list[str]
    updated_focus_areas: list[FocusArea]
    recommended_next_actions: list[str]
    submission_id: str | None = None
    pipeline_refreshed: bool = False
    updated_plan_ready_for_pdf: bool = False


class ESGReportDisclosure(BaseModel):
    disclosure: str
    title: str
    computed: bool
    value: Any = None
    unit: str | None = None
    reason_for_omission: str | None = None


class ESGReportResponse(BaseModel):
    company_id: str
    generated_at: datetime
    disclosures: list[ESGReportDisclosure]
    reasons_for_omission: list[OmissionReason] = Field(default_factory=list)
    source_submission_id: str | None = None
