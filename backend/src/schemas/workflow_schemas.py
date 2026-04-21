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


class UploadedFileRecord(BaseModel):
    file_id: str
    filename: str
    media_type: str
    size_bytes: int = Field(ge=0)
    uploaded_at: datetime


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


class FileExtractionResponse(BaseModel):
    company_id: str
    files: list[UploadedFileRecord]
    extracted_metrics: list[ExtractedMetric]
    ai_summary: str
    follow_up_questions: list[str]


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


class QuickWinItem(BaseModel):
    title: str
    impact_area: str
    effort: Literal["low", "medium"]
    expected_benefit: str
    why_recommended: str
    first_step: str


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
