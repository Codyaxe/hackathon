from __future__ import annotations

import hashlib
import io
from datetime import datetime, timezone
import json
import logging
from pathlib import Path
import re
from typing import Any, Literal, Sequence, cast
from uuid import uuid4
import xml.etree.ElementTree as ET
import zipfile

from fastapi import HTTPException, Request, UploadFile
from fastapi.encoders import jsonable_encoder
from google.genai import types
from pydantic import BaseModel, Field

from src.dependencies.repository import ESGRepository
from src.schemas.MetricsSchemas.GRI_302_Metrics import (
    ConversionFactors,
    EnergyEntry,
    Omission302,
)
from src.schemas.MetricsSchemas.GRI_305_Metrics import (
    EmissionEntry,
    EmissionFactorMetadata,
    Omission305,
)
from src.schemas.MetricsSchemas.GRI_401_Metrics import Omission401
from src.schemas.output_schemas import (
    AIExtracted_GRI_302,
    AIExtracted_GRI_305,
    AIExtracted_GRI_401,
)
from src.schemas.workflow_schemas import (
    AIFileExtractionResult,
    DashboardKPI,
    ESGReportDisclosure,
    ESGReportResponse,
    ESGPlanAction,
    ESGPlanRequest,
    ESGPlanResponse,
    EvidenceFileRecord,
    EvidenceListResponse,
    ExtractedMetric,
    FileExtractionResponse,
    FixedExtractionMetrics,
    FocusArea,
    MonthlyUpdateQuestion,
    MonthlyUpdateQuestionsResponse,
    MonthlyUpdateResponse,
    MonthlyUpdateSubmission,
    OmissionReason,
    OnboardingQuizResponse,
    OnboardingQuizSubmission,
    OnboardingRecommendationResponse,
    ProgressStep,
    ProgressTrackerResponse,
    QuickWinItem,
    QuickWinsResponse,
    ResponseLibraryEntry,
    ResponseLibraryResponse,
    UploadedFileRecord,
    WorkflowQuestion,
)


FocusAreaName = Literal[
    "energy",
    "emissions",
    "waste",
    "workforce",
    "governance",
    "data_foundation",
    "supply_chain",
]
FocusPriority = Literal["high", "medium", "low"]

logger = logging.getLogger(__name__)


class AIQuickWinsPayload(BaseModel):
    quick_wins: list[QuickWinItem] = Field(default_factory=list)


class ESGWorkflowService:
    """Application service for onboarding, planning, uploads, and progress workflows."""

    _quick_wins_cache: dict[str, dict[str, Any]] = {}

    SUPPORTED_MEDIA_TYPES = {
        "application/pdf",
        "text/csv",
        "text/plain",
        "application/vnd.ms-excel",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "image/png",
        "image/jpeg",
        "image/jpg",
        "image/webp",
    }

    def __init__(self, request: Request):
        self.request = request
        self.ai = request.app.state.ai
        self.repo = ESGRepository(Path(request.app.state.workflow_storage_path))
        self.GRI302Engine = request.app.state.GRI302Engine
        self.GRI305Engine = request.app.state.GRI305Engine
        self.GRI401Engine = request.app.state.GRI401Engine
        self.evidence_root = (
            Path(request.app.state.workflow_storage_path).parent / "evidence"
        )
        self.evidence_root.mkdir(parents=True, exist_ok=True)

    def get_onboarding_quiz(self, context) -> OnboardingQuizResponse:
        questions = self._build_onboarding_questions(
            context.industry, context.employee_count
        )
        return OnboardingQuizResponse(context=context, questions=questions)

    async def submit_onboarding(
        self, submission: OnboardingQuizSubmission
    ) -> OnboardingRecommendationResponse:
        answers = self._answers_to_map(submission.answers)
        focus_areas = self._recommend_focus_areas(
            submission.context.industry, submission.context.employee_count, answers
        )

        fallback_summary = (
            "Focus first on the top ESG themes below, then establish a monthly data routine "
            "to keep reporting simple and consistent."
        )
        summary_prompt = (
            "You are an ESG advisor for SMEs.\n"
            "Write a concise recommendation for a dashboard card.\n"
            "Output plain text only (no markdown, no JSON, no bullet or numbered list symbols).\n"
            "Keep it practical and non-technical in exactly 3-4 short sentences.\n"
            "Do not add intro labels like 'Here is' or 'Recommendation'.\n\n"
            f"Industry: {submission.context.industry}\n"
            f"Employee count: {submission.context.employee_count}\n"
            f"Top focus areas: {[f.area for f in focus_areas]}\n"
            f"Answers: {answers}"
        )
        recommendation_summary = await self._safe_ai_summary(
            summary_prompt, fallback_summary, max_sentences=4
        )
        next_steps = self._build_next_steps(focus_areas)

        onboarding_payload = {
            "submitted_at": self._utc_now_iso(),
            "answers": answers,
            "focus_areas": [area.model_dump() for area in focus_areas],
            "recommendation_summary": recommendation_summary,
            "next_steps": next_steps,
        }

        self.repo.save_profile(
            submission.context.company_id, submission.context.model_dump(mode="json")
        )
        self.repo.save_onboarding(submission.context.company_id, onboarding_payload)
        self.repo.append_library_entry(
            submission.context.company_id, "onboarding", onboarding_payload
        )

        return OnboardingRecommendationResponse(
            company_id=submission.context.company_id,
            focus_areas=focus_areas,
            recommendation_summary=recommendation_summary,
            next_steps=next_steps,
        )

    async def generate_plan(self, plan_request: ESGPlanRequest) -> ESGPlanResponse:
        company_data = self.repo.get_company_data(plan_request.company_id)
        if not company_data:
            raise HTTPException(
                status_code=404, detail="Company not found. Complete onboarding first."
            )

        profile = company_data.get("profile", {})
        onboarding = company_data.get("onboarding", {})
        focus_areas = onboarding.get("focus_areas", [])

        selected_themes = [
            theme.lower().strip()
            for theme in plan_request.preferred_focus_areas
            if theme.strip()
        ]
        if not selected_themes:
            selected_themes = [area.get("area", "") for area in focus_areas][:4]
        if not selected_themes:
            selected_themes = self._default_focus_by_industry(
                profile.get("industry", "")
            )[:4]

        selected_themes = [theme for theme in selected_themes if theme]
        actions = self._build_plan_actions(selected_themes)

        fallback_summary = (
            "This one-page ESG plan prioritizes actions that are easy to adopt first, while building "
            "a reliable monthly data baseline for future reporting."
        )
        plan_prompt = (
            "You are generating a structured ESG action plan.\n"
            "Output plain text only (no markdown symbols, no JSON, no code fences).\n"
            "Keep it concise and directly usable in a web dashboard.\n"
            "Use this format exactly:\n"
            "Plan overview: <2-3 sentences>\n"
            "Immediate focus: <1-2 sentences>\n"
            "Execution guidance: <1-2 sentences>\n\n"
            f"Company: {profile.get('company_name', 'This company')}\n"
            f"Industry: {profile.get('industry', 'Unknown')}\n"
            f"Employees: {profile.get('employee_count', 'Unknown')}\n"
            f"Focus areas: {', '.join(selected_themes)}\n\n"
            "Action details:\n"
            + "\n".join(
                f"- {a.title} | {a.why_it_matters} | owner: {a.owner} | metric: {a.success_metric} | weeks: {a.timeline_weeks}"
                for a in actions
            )
        )
        one_page_summary = await self._safe_ai_summary(
            plan_prompt, fallback_summary, max_sentences=8
        )

        monthly_questions = [
            "What changed most in your energy or fuel usage this month?",
            "Which ESG action moved forward, and what blocked progress?",
            "What one low-effort improvement can you complete next month?",
        ]

        latest_submission = self.repo.get_latest_submission(plan_request.company_id)
        latest_report = self.repo.get_latest_report(plan_request.company_id)
        kpis = self._kpi_labels_from_submission(latest_submission)
        ready_for_pdf = bool(latest_report and latest_report.get("disclosures"))

        plan_response = ESGPlanResponse(
            company_id=plan_request.company_id,
            generated_at=datetime.now(timezone.utc),
            one_page_summary=one_page_summary,
            priority_themes=selected_themes,
            actions=actions,
            monthly_check_in_questions=monthly_questions,
            kpis=kpis,
            ready_for_pdf=ready_for_pdf,
        )

        plan_payload = plan_response.model_dump(mode="json")
        self.repo.save_plan(plan_request.company_id, plan_payload)
        self.repo.append_library_entry(plan_request.company_id, "plan", plan_payload)

        return plan_response

    async def upload_files(
        self,
        company_id: str,
        files: list[UploadFile],
        notes: str | None = None,
    ) -> FileExtractionResponse:
        if not files:
            raise HTTPException(
                status_code=400, detail="At least one file is required."
            )

        company_data = self.repo.get_company_data(company_id) or {}

        file_parts: list[types.Part] = [
            types.Part.from_text(
                text=(
                    "Extract ESG-relevant metrics from these files. Return concise JSON only with: "
                    "summary, metrics[], follow_up_questions[]."
                )
            )
        ]
        if notes:
            file_parts.append(types.Part.from_text(text=f"User notes: {notes}"))
        text_previews: list[str] = []

        upload_records: list[UploadedFileRecord] = []
        evidence_records: list[dict[str, Any]] = []

        for upload in files:
            binary = await upload.read()
            if not binary:
                continue

            media_type = self._normalize_media_type(upload)
            if not self._is_supported_upload(upload.filename or "", media_type):
                raise HTTPException(
                    status_code=400,
                    detail=(
                        f"Unsupported file type for '{upload.filename}'. "
                        "Supported: PDF, images, CSV, and Excel files."
                    ),
                )

            record = UploadedFileRecord(
                file_id=str(uuid4()),
                filename=upload.filename or "uploaded-file",
                media_type=media_type,
                size_bytes=len(binary),
                uploaded_at=datetime.now(timezone.utc),
                disclosure_tag=self._infer_disclosure_tag(upload.filename or "", notes),
            )
            upload_records.append(record)

            storage_path = self._save_evidence_bytes(
                company_id=company_id,
                file_id=record.file_id,
                binary=binary,
            )
            evidence_payload = {
                **EvidenceFileRecord(
                    file_id=record.file_id,
                    filename=record.filename,
                    media_type=record.media_type,
                    size_bytes=record.size_bytes,
                    uploaded_at=record.uploaded_at,
                    disclosure_tag=record.disclosure_tag,
                ).model_dump(mode="json"),
                "storage_path": storage_path,
            }
            self.repo.save_evidence_file(company_id, evidence_payload)
            evidence_records.append(evidence_payload)

            if media_type in {"text/csv", "text/plain"}:
                text_preview = binary.decode("utf-8", errors="ignore")[:20000]
                text_previews.append(text_preview)
                file_parts.append(
                    types.Part.from_text(
                        text=f"File: {record.filename}\nContent preview:\n{text_preview}"
                    )
                )
            elif media_type in {
                "application/vnd.ms-excel",
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            }:
                spreadsheet_preview = self._extract_spreadsheet_preview(binary)
                if spreadsheet_preview:
                    text_previews.append(spreadsheet_preview)
                    file_parts.append(
                        types.Part.from_text(
                            text=(
                                f"Spreadsheet: {record.filename}\n"
                                f"Extracted cell preview:\n{spreadsheet_preview[:20000]}"
                            )
                        )
                    )
                else:
                    file_parts.append(
                        types.Part.from_text(
                            text=(
                                f"Spreadsheet: {record.filename}\n"
                                "Unable to parse spreadsheet preview locally. "
                                "Proceeding without raw spreadsheet bytes because this MIME type is not accepted by Gemini content API."
                            )
                        )
                    )
            else:
                file_parts.append(
                    types.Part.from_bytes(data=binary, mime_type=media_type)
                )

        if not upload_records:
            raise HTTPException(
                status_code=400, detail="No readable files were uploaded."
            )

        logger.info(
            "Upload received for company_id=%s with %d files. AI client ready=%s",
            company_id,
            len(upload_records),
            self.ai is not None,
        )

        combined_preview = "\n\n".join(text_previews).strip()
        extraction = await self._extract_metrics_with_ai(
            file_parts,
            upload_records,
            text_preview=combined_preview,
        )
        fixed_extraction = await self._extract_fixed_metrics_with_ai(
            file_parts=file_parts,
            fallback_headcount=company_data.get("profile", {}).get("employee_count"),
            text_preview=combined_preview,
        )
        logger.info(
            "Fixed extraction for company_id=%s -> electricity_kwh=%s diesel_liters=%s waste_kg=%s headcount=%s new_hires=%s turnover_count=%s missing=%s",
            company_id,
            fixed_extraction.electricity_kwh,
            fixed_extraction.diesel_liters,
            fixed_extraction.waste_kg,
            fixed_extraction.headcount,
            fixed_extraction.new_hires,
            fixed_extraction.turnover_count,
            fixed_extraction.missing_fields,
        )

        pipeline_submission = self._run_submission_pipeline(
            company_id=company_id,
            company_data=company_data,
            fixed_extraction=fixed_extraction,
            source="upload",
            month=None,
            changes=None,
            notes=notes,
            evidence_records=evidence_records,
        )

        response = FileExtractionResponse(
            company_id=company_id,
            files=upload_records,
            extracted_metrics=extraction.metrics,
            ai_summary=extraction.summary,
            follow_up_questions=extraction.follow_up_questions,
            fixed_extraction=fixed_extraction,
        )

        response_payload = response.model_dump(mode="json")
        self.repo.save_upload_batch(
            company_id,
            upload_records=[
                record.model_dump(mode="json") for record in upload_records
            ],
            extraction_payload=response_payload,
        )
        response_payload["submission_id"] = pipeline_submission.get("submission_id")
        self.repo.append_library_entry(
            company_id, "upload_extraction", response_payload
        )

        return response

    def get_response_library(
        self, company_id: str, limit: int = 50
    ) -> ResponseLibraryResponse:
        entries_raw = self.repo.get_library_entries(company_id, limit=limit)
        entries = [ResponseLibraryEntry.model_validate(item) for item in entries_raw]
        return ResponseLibraryResponse(company_id=company_id, entries=entries)

    def reset_reporting_artifacts(self, company_id: str) -> dict[str, Any]:
        company_data = self.repo.get_company_data(company_id)
        if not company_data:
            raise HTTPException(
                status_code=404, detail="Company not found. Complete onboarding first."
            )

        updated = self.repo.reset_reporting_artifacts(company_id)
        if not updated:
            raise HTTPException(status_code=404, detail="Company not found.")

        return {
            "company_id": company_id,
            "status": "reset",
            "message": "GRI disclosures, KPI snapshots, and submission artifacts were reset.",
        }

    def list_evidence(self, company_id: str) -> EvidenceListResponse:
        company_data = self.repo.get_company_data(company_id)
        if not company_data:
            raise HTTPException(
                status_code=404, detail="Company not found. Complete onboarding first."
            )

        evidence_files: list[EvidenceFileRecord] = []
        for item in self.repo.get_evidence_files(company_id):
            evidence_files.append(EvidenceFileRecord.model_validate(item))

        return EvidenceListResponse(
            company_id=company_id, evidence_files=evidence_files
        )

    def resolve_evidence_file(
        self, company_id: str, file_id: str
    ) -> tuple[Path, dict[str, Any]]:
        metadata = self.repo.get_evidence_file(company_id, file_id)
        if not metadata:
            raise HTTPException(status_code=404, detail="Evidence file not found.")

        raw_path = metadata.get("storage_path")
        if not raw_path:
            raise HTTPException(
                status_code=404, detail="Evidence storage path is missing."
            )

        file_path = Path(raw_path)
        if not file_path.exists() or not file_path.is_file():
            raise HTTPException(
                status_code=404, detail="Evidence file content is unavailable."
            )

        return file_path, metadata

    def delete_evidence_file(self, company_id: str, file_id: str) -> None:
        metadata = self.repo.get_evidence_file(company_id, file_id)
        if not metadata:
            raise HTTPException(status_code=404, detail="Evidence file not found.")

        raw_path = metadata.get("storage_path")
        if raw_path:
            file_path = Path(raw_path)
            try:
                if file_path.exists() and file_path.is_file():
                    file_path.unlink()
            except OSError as exc:
                raise HTTPException(
                    status_code=500,
                    detail="Failed to delete evidence file content.",
                ) from exc

        removed = self.repo.delete_evidence_file(company_id, file_id)
        if removed is None:
            raise HTTPException(status_code=404, detail="Evidence file not found.")

    def get_esg_report(self, company_id: str) -> ESGReportResponse:
        company_data = self.repo.get_company_data(company_id)
        if not company_data:
            raise HTTPException(
                status_code=404, detail="Company not found. Complete onboarding first."
            )

        latest_report = self.repo.get_latest_report(company_id)
        if latest_report:
            return ESGReportResponse.model_validate(latest_report)

        latest_submission = self.repo.get_latest_submission(company_id)
        if not latest_submission:
            raise HTTPException(
                status_code=404,
                detail="No submission data found yet. Upload evidence or run monthly checkup first.",
            )

        report_payload = self._build_report_payload(company_id, latest_submission)
        self.repo.save_latest_report(company_id, report_payload)
        return ESGReportResponse.model_validate(report_payload)

    def get_esg_report_pdf(self, company_id: str) -> tuple[str, bytes]:
        report = self.get_esg_report(company_id)
        company_data = self.repo.get_company_data(company_id) or {}
        profile = company_data.get("profile", {})

        lines: list[str] = [
            f"ESG Report - {profile.get('company_name', company_id)}",
            f"Industry: {profile.get('industry', 'Unknown')}",
            f"Location: {profile.get('location', 'Unknown')}",
            f"Generated at: {report.generated_at.isoformat()}",
            "",
            "GRI Disclosures",
        ]

        for disclosure in report.disclosures:
            if disclosure.computed:
                lines.append(
                    f"{disclosure.disclosure} {disclosure.title}: {self._stringify_report_value(disclosure.value)} {disclosure.unit or ''}".strip()
                )
            else:
                lines.append(
                    f"{disclosure.disclosure} {disclosure.title}: OMITTED - {disclosure.reason_for_omission or 'Not enough data.'}"
                )

        if report.reasons_for_omission:
            lines.append("")
            lines.append("Reasons for Omission")
            for omission in report.reasons_for_omission:
                lines.append(f"{omission.disclosure}: {omission.reason}")

        pdf_bytes = self._build_simple_pdf(lines)
        filename = f"{company_id}-esg-report-{datetime.now(timezone.utc).strftime('%Y%m%d')}.pdf"
        return filename, pdf_bytes

    def get_progress(self, company_id: str) -> ProgressTrackerResponse:
        company_data = self.repo.get_company_data(company_id)
        if not company_data:
            raise HTTPException(
                status_code=404, detail="Company not found. Complete onboarding first."
            )

        uploads = company_data.get("uploads", [])
        extractions = company_data.get("extractions", [])
        monthly_updates = company_data.get("monthly_updates", [])

        has_onboarding = bool(company_data.get("onboarding"))
        has_uploads = len(uploads) > 0
        has_baseline = any(batch.get("extracted_metrics") for batch in extractions)
        has_plan = bool(company_data.get("plan"))
        current_month = datetime.now(timezone.utc).strftime("%Y-%m")
        has_monthly_update = any(
            item.get("month") == current_month for item in monthly_updates
        )

        steps = [
            ProgressStep(
                step_id="onboarding",
                title="Onboarding completed",
                completed=has_onboarding,
                score=100 if has_onboarding else 0,
                improvement_tip="Answer the onboarding questions to personalize ESG priorities.",
            ),
            ProgressStep(
                step_id="uploads",
                title="Source files uploaded",
                completed=has_uploads,
                score=min(100, len(uploads) * 25),
                improvement_tip="Upload at least utility bills, invoices, or payroll/workforce records.",
            ),
            ProgressStep(
                step_id="baseline",
                title="Baseline metrics extracted",
                completed=has_baseline,
                score=100 if has_baseline else (40 if has_uploads else 0),
                improvement_tip="Run extraction so you can compare month-over-month performance.",
            ),
            ProgressStep(
                step_id="plan",
                title="Action plan generated",
                completed=has_plan,
                score=100 if has_plan else 0,
                improvement_tip="Generate your one-page ESG plan from onboarding + upload insights.",
            ),
            ProgressStep(
                step_id="monthly_update",
                title="Current month update submitted",
                completed=has_monthly_update,
                score=100 if has_monthly_update else 0,
                improvement_tip="Submit this month's quick update to keep recommendations fresh.",
            ),
        ]

        completion = round(
            sum(step.score for step in steps) / (len(steps) * 100) * 100, 1
        )
        if completion < 30:
            maturity = "getting_started"
        elif completion < 60:
            maturity = "building_baseline"
        elif completion < 85:
            maturity = "improving"
        else:
            maturity = "advanced"

        next_actions = [step.improvement_tip for step in steps if not step.completed][
            :3
        ]

        dashboard_snapshot = self.repo.get_latest_dashboard(company_id) or {}
        kpis: list[DashboardKPI] = [
            DashboardKPI.model_validate(item)
            for item in dashboard_snapshot.get("kpis", [])
        ]

        # If no dashboard snapshot yet, build initial KPIs from latest extraction
        if not kpis and extractions:
            latest_extraction = extractions[-1] if extractions else {}
            fixed_metrics = latest_extraction.get("fixed_extraction")
            computations = latest_extraction.get("computations", {})

            if fixed_metrics and computations:
                initial_dashboard = self._build_dashboard_from_results(
                    FixedExtractionMetrics.model_validate(fixed_metrics), computations
                )
                kpis = [
                    DashboardKPI.model_validate(item)
                    for item in initial_dashboard.get("kpis", [])
                ]

        esg_score = self._to_float(dashboard_snapshot.get("esg_score"))
        if esg_score is None:
            esg_score = completion
        compliance_status = str(
            dashboard_snapshot.get("compliance_status", "Needs Attention")
        )
        if compliance_status not in {"On Track", "Needs Attention"}:
            compliance_status = "Needs Attention"

        quick_wins: list[QuickWinItem] = []

        return ProgressTrackerResponse(
            company_id=company_id,
            completion_percentage=completion,
            maturity_stage=maturity,
            steps=steps,
            next_best_actions=next_actions,
            esg_score=esg_score,
            compliance_status=cast(
                Literal["On Track", "Needs Attention"], compliance_status
            ),
            kpis=kpis,
            quick_wins_with_savings=quick_wins,
        )

    async def get_quick_wins(self, company_id: str) -> QuickWinsResponse:
        company_data = self.repo.get_company_data(company_id)
        if not company_data:
            raise HTTPException(
                status_code=404, detail="Company not found. Complete onboarding first."
            )

        has_evidence = bool(self.repo.get_evidence_files(company_id))
        has_uploads = bool(company_data.get("uploads", []))
        if not has_evidence and not has_uploads:
            return QuickWinsResponse(
                company_id=company_id,
                generated_at=datetime.now(timezone.utc),
                quick_wins=[],
            )

        latest_submission = self.repo.get_latest_submission(company_id) or {}
        dashboard = latest_submission.get("dashboard", {})
        kpis = dashboard.get("kpis", [])
        fixed_extraction = latest_submission.get("fixed_extraction", {})
        evidence_files = self.repo.get_evidence_files(company_id)

        context_hash = self._hash_quick_wins_context(
            evidence_files=evidence_files,
            kpis=kpis,
            fixed_extraction=fixed_extraction,
        )

        cached = self._quick_wins_cache.get(company_id)
        if cached and cached.get("context_hash") == context_hash:
            return QuickWinsResponse(
                company_id=company_id,
                generated_at=datetime.now(timezone.utc),
                quick_wins=cached.get("quick_wins", []),
            )

        quick_wins = await self._generate_ai_quick_wins(
            company_id=company_id,
            company_data=company_data,
            kpis=kpis,
            fixed_extraction=fixed_extraction,
            evidence_files=evidence_files,
        )

        if quick_wins is not None:
            self._quick_wins_cache[company_id] = {
                "context_hash": context_hash,
                "quick_wins": quick_wins,
            }
        elif cached:
            quick_wins = cached.get("quick_wins", [])
        else:
            quick_wins = []

        return QuickWinsResponse(
            company_id=company_id,
            generated_at=datetime.now(timezone.utc),
            quick_wins=quick_wins,
        )

    async def _generate_ai_quick_wins(
        self,
        company_id: str,
        company_data: dict[str, Any],
        kpis: list[dict[str, Any]],
        fixed_extraction: dict[str, Any],
        evidence_files: list[dict[str, Any]],
    ) -> list[QuickWinItem] | None:
        if self.ai is None:
            logger.info(
                "AI unavailable; quick wins skipped for company_id=%s", company_id
            )
            return None

        profile = company_data.get("profile", {})
        onboarding = company_data.get("onboarding", {})
        focus_areas = [
            item.get("area", "")
            for item in onboarding.get("focus_areas", [])
            if item.get("area")
        ]

        evidence_summary = [
            {
                "filename": item.get("filename"),
                "media_type": item.get("media_type"),
                "disclosure_tag": item.get("disclosure_tag"),
            }
            for item in evidence_files[:15]
        ]

        prompt = (
            "You are an ESG advisor for SMEs. Generate practical quick wins based on uploaded evidence and KPI context. "
            "Return JSON only with key quick_wins as an array of 1-5 items.\n"
            "Each quick win must strictly match fields: "
            "title, impact_area, effort (low|medium), expected_benefit, why_recommended, first_step, estimated_cost_savings_php.\n"
            "Use only evidence-backed suggestions from the context below. "
            "If context is insufficient, return an empty quick_wins array.\n\n"
            f"Company profile: {json.dumps(profile, ensure_ascii=True)}\n"
            f"Focus areas: {json.dumps(focus_areas, ensure_ascii=True)}\n"
            f"Latest KPI snapshot: {json.dumps(kpis, ensure_ascii=True)}\n"
            f"Latest fixed extraction: {json.dumps(fixed_extraction, ensure_ascii=True)}\n"
            f"Evidence files: {json.dumps(evidence_summary, ensure_ascii=True)}"
        )

        try:
            response = await self.ai.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=AIQuickWinsPayload,
                ),
            )
            if response.parsed is not None:
                return response.parsed.quick_wins[:5]
        except Exception:
            logger.exception(
                "AI quick wins generation failed for company_id=%s.",
                company_id,
            )

        return None

    def _hash_quick_wins_context(
        self,
        evidence_files: list[dict[str, Any]],
        kpis: list[dict[str, Any]],
        fixed_extraction: dict[str, Any],
    ) -> str:
        evidence_summary = [
            {
                "filename": item.get("filename"),
                "media_type": item.get("media_type"),
                "disclosure_tag": item.get("disclosure_tag"),
                "size_bytes": item.get("size_bytes"),
                "uploaded_at": item.get("uploaded_at"),
            }
            for item in evidence_files
        ]
        canonical_payload = {
            "evidence": evidence_summary,
            "kpis": kpis,
            "fixed_extraction": fixed_extraction,
        }
        serialized = json.dumps(canonical_payload, sort_keys=True, ensure_ascii=True)
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()

    def get_monthly_update_questions(
        self,
        company_id: str,
        month: str | None = None,
    ) -> MonthlyUpdateQuestionsResponse:
        company_data = self.repo.get_company_data(company_id)
        if not company_data:
            raise HTTPException(
                status_code=404, detail="Company not found. Complete onboarding first."
            )

        resolved_month = month or datetime.now(timezone.utc).strftime("%Y-%m")
        self._validate_month(resolved_month)

        focus_areas = [
            item.get("area", "")
            for item in company_data.get("onboarding", {}).get("focus_areas", [])
        ]
        questions: list[MonthlyUpdateQuestion] = [
            MonthlyUpdateQuestion(
                question_id="mq_energy_change_pct",
                prompt="How did total energy usage change compared to last month (%)?",
                field_name="energy_change_pct",
                input_type="number",
            ),
            MonthlyUpdateQuestion(
                question_id="mq_fuel_or_logistics_change",
                prompt="Did fuel usage or logistics activity materially change this month?",
                field_name="fuel_or_logistics_change",
                input_type="single_choice",
                options=["increased", "decreased", "no_change", "unknown"],
            ),
            MonthlyUpdateQuestion(
                question_id="mq_major_esg_action",
                prompt="What was the most important ESG action completed this month?",
                field_name="major_esg_action",
                input_type="text",
            ),
        ]

        if "workforce" in focus_areas:
            questions.append(
                MonthlyUpdateQuestion(
                    question_id="mq_workforce_incidents",
                    prompt="Any workforce safety or retention issue this month?",
                    field_name="workforce_issue",
                    input_type="boolean",
                )
            )

        if "waste" in focus_areas:
            questions.append(
                MonthlyUpdateQuestion(
                    question_id="mq_waste_change_pct",
                    prompt="How did landfill waste volume change this month (%)?",
                    field_name="waste_change_pct",
                    input_type="number",
                )
            )

        return MonthlyUpdateQuestionsResponse(
            company_id=company_id,
            month=resolved_month,
            context_message="Share only what changed this month; no full re-onboarding needed.",
            questions=questions,
        )

    async def submit_monthly_update(
        self, submission: MonthlyUpdateSubmission
    ) -> MonthlyUpdateResponse:
        self._validate_month(submission.month)

        company_data = self.repo.get_company_data(submission.company_id)
        if not company_data:
            raise HTTPException(
                status_code=404, detail="Company not found. Complete onboarding first."
            )

        summary = [
            f"{key.replace('_', ' ').capitalize()}: {value}"
            for key, value in submission.changes.items()
        ]
        if submission.notes:
            summary.append(f"Notes: {submission.notes}")
        if not summary:
            summary.append("No major operational changes reported.")

        updated_focus = self._refresh_focus_from_changes(
            existing_focus=company_data.get("onboarding", {}).get("focus_areas", []),
            changes=submission.changes,
        )

        recommended_next_actions = self._next_actions_from_changes(submission.changes)

        payload = {
            "month": submission.month,
            "changes": submission.changes,
            "notes": submission.notes,
            "change_summary": summary,
            "updated_focus_areas": [item.model_dump() for item in updated_focus],
            "recommended_next_actions": recommended_next_actions,
            "submitted_at": self._utc_now_iso(),
        }

        fixed_extraction = self._fixed_metrics_from_changes(
            changes=submission.changes,
            fallback_headcount=company_data.get("profile", {}).get("employee_count"),
        )
        pipeline_submission = self._run_submission_pipeline(
            company_id=submission.company_id,
            company_data=company_data,
            fixed_extraction=fixed_extraction,
            source="monthly_update",
            month=submission.month,
            changes=submission.changes,
            notes=submission.notes,
            evidence_records=[],
        )

        plan_ready_for_pdf = False
        if company_data.get("plan"):
            refreshed_plan = await self._refresh_plan_from_latest_pipeline(
                company_id=submission.company_id,
                company_data=company_data,
            )
            plan_ready_for_pdf = bool(refreshed_plan.get("ready_for_pdf", False))

        self.repo.save_monthly_update(submission.company_id, payload)
        self.repo.append_library_entry(submission.company_id, "monthly_update", payload)

        return MonthlyUpdateResponse(
            company_id=submission.company_id,
            month=submission.month,
            change_summary=summary,
            updated_focus_areas=updated_focus,
            recommended_next_actions=recommended_next_actions,
            submission_id=pipeline_submission.get("submission_id"),
            pipeline_refreshed=True,
            updated_plan_ready_for_pdf=plan_ready_for_pdf,
        )

    async def submit_monthly_update_with_files(
        self,
        submission: MonthlyUpdateSubmission,
        files: list[UploadFile],
    ) -> MonthlyUpdateResponse:
        await self.upload_files(
            company_id=submission.company_id,
            files=files,
            notes=submission.notes,
        )
        return await self.submit_monthly_update(submission)

    def _build_onboarding_questions(
        self, industry: str, employee_count: int
    ) -> list[WorkflowQuestion]:
        questions = [
            WorkflowQuestion(
                question_id="q_tracks_energy_data",
                prompt="Do you currently track electricity or fuel consumption monthly?",
                field_name="tracks_energy_data",
                input_type="boolean",
            ),
            WorkflowQuestion(
                question_id="q_tracks_emissions_data",
                prompt="Do you currently estimate or track carbon emissions?",
                field_name="tracks_emissions_data",
                input_type="boolean",
            ),
            WorkflowQuestion(
                question_id="q_has_waste_tracking",
                prompt="Do you track landfill vs recycled waste?",
                field_name="has_waste_tracking",
                input_type="boolean",
            ),
            WorkflowQuestion(
                question_id="q_top_pain_points",
                prompt="What are your biggest ESG pain points right now?",
                field_name="top_pain_points",
                input_type="multi_choice",
                options=[
                    "energy_costs",
                    "customer_requirements",
                    "regulatory_pressure",
                    "limited_team_time",
                    "missing_data",
                ],
            ),
            WorkflowQuestion(
                question_id="q_has_supplier_code",
                prompt="Do you already require suppliers to meet sustainability criteria?",
                field_name="has_supplier_code",
                input_type="boolean",
            ),
        ]

        normalized = industry.lower()
        if "manufact" in normalized or "industrial" in normalized:
            questions.append(
                WorkflowQuestion(
                    question_id="q_has_process_emissions",
                    prompt="Do you have combustion/process activities that may create direct emissions?",
                    field_name="has_process_emissions",
                    input_type="boolean",
                )
            )

        if employee_count > 150:
            questions.append(
                WorkflowQuestion(
                    question_id="q_has_esg_owner",
                    prompt="Do you have a clearly assigned ESG owner internally?",
                    field_name="has_esg_owner",
                    input_type="boolean",
                )
            )

        return questions

    def _answers_to_map(self, answers) -> dict[str, Any]:
        return {answer.question_id: answer.value for answer in answers}

    def _default_focus_by_industry(self, industry: str) -> list[FocusAreaName]:
        normalized = industry.lower()
        if "manufact" in normalized or "industrial" in normalized:
            return ["energy", "emissions", "waste", "workforce", "data_foundation"]
        if "retail" in normalized:
            return ["energy", "waste", "supply_chain", "governance", "data_foundation"]
        if "logistics" in normalized or "transport" in normalized:
            return [
                "emissions",
                "energy",
                "supply_chain",
                "governance",
                "data_foundation",
            ]
        if "tech" in normalized or "software" in normalized:
            return ["energy", "workforce", "governance", "data_foundation"]
        return ["energy", "emissions", "workforce", "governance", "data_foundation"]

    def _recommend_focus_areas(
        self, industry: str, employee_count: int, answers: dict[str, Any]
    ) -> list[FocusArea]:
        scores: dict[FocusAreaName, int] = {
            "energy": 0,
            "emissions": 0,
            "waste": 0,
            "workforce": 0,
            "governance": 0,
            "data_foundation": 0,
            "supply_chain": 0,
        }
        reasons: dict[FocusAreaName, list[str]] = {key: [] for key in scores}

        for area in self._default_focus_by_industry(industry):
            scores[area] += 3
            reasons[area].append(f"Common priority for {industry} SMEs.")

        if employee_count <= 50:
            scores["data_foundation"] += 3
            reasons["data_foundation"].append(
                "Smaller teams benefit most from lightweight monthly data templates."
            )
        elif employee_count >= 250:
            scores["governance"] += 2
            scores["supply_chain"] += 2
            reasons["governance"].append(
                "Larger operations usually need ownership and controls to stay consistent."
            )
            reasons["supply_chain"].append(
                "Bigger supplier ecosystems increase ESG dependency risk."
            )

        if not bool(answers.get("q_tracks_energy_data", False)):
            scores["energy"] += 2
            scores["data_foundation"] += 2
            reasons["energy"].append("Energy is currently not tracked monthly.")
            reasons["data_foundation"].append(
                "Data gaps are blocking consistent progress measurement."
            )

        if not bool(answers.get("q_tracks_emissions_data", False)):
            scores["emissions"] += 2
            reasons["emissions"].append("No emissions baseline yet.")

        if not bool(answers.get("q_has_waste_tracking", False)):
            scores["waste"] += 2
            reasons["waste"].append("Waste streams are not currently measured.")

        if not bool(answers.get("q_has_supplier_code", False)):
            scores["supply_chain"] += 2
            reasons["supply_chain"].append(
                "Supplier sustainability controls are not formalized."
            )

        if bool(answers.get("q_has_process_emissions", False)):
            scores["emissions"] += 2
            reasons["emissions"].append(
                "Operational processes likely create direct emissions."
            )

        if not bool(answers.get("q_has_esg_owner", True)):
            scores["governance"] += 2
            reasons["governance"].append("No clear ESG owner assigned internally.")

        pain_points = answers.get("q_top_pain_points", [])
        if isinstance(pain_points, str):
            pain_points = [pain_points]

        if "energy_costs" in pain_points:
            scores["energy"] += 2
            reasons["energy"].append(
                "Rising energy costs were reported as a major pain point."
            )
        if "customer_requirements" in pain_points:
            scores["governance"] += 1
            scores["supply_chain"] += 1
            reasons["governance"].append(
                "Customer requirements often require evidence and documented processes."
            )
        if "missing_data" in pain_points:
            scores["data_foundation"] += 2
            reasons["data_foundation"].append(
                "Missing data is directly slowing ESG execution."
            )

        ranked = sorted(scores.items(), key=lambda item: item[1], reverse=True)
        top_ranked: list[tuple[FocusAreaName, int]] = [
            item for item in ranked if item[1] > 0
        ][:4]
        if not top_ranked:
            top_ranked = [("data_foundation", 1)]

        focus: list[FocusArea] = []
        for area, score in top_ranked:
            priority: FocusPriority
            if score >= 6:
                priority = "high"
            elif score >= 4:
                priority = "medium"
            else:
                priority = "low"

            area_reasons = reasons[area] or [
                "Relevant for your current ESG maturity stage."
            ]
            reason_text = " ".join(dict.fromkeys(area_reasons))
            focus.append(FocusArea(area=area, priority=priority, reason=reason_text))

        return focus

    def _build_next_steps(self, focus_areas: list[FocusArea]) -> list[str]:
        steps = []
        for area in focus_areas[:3]:
            if area.area == "energy":
                steps.append("Start a monthly utility and fuel tracker with one owner.")
            elif area.area == "emissions":
                steps.append(
                    "Create your first Scope 1 and Scope 2 baseline using existing bills."
                )
            elif area.area == "waste":
                steps.append(
                    "Track landfill vs recycled waste by volume or weight each month."
                )
            elif area.area == "workforce":
                steps.append(
                    "Add a lightweight monthly workforce wellbeing and safety check-in."
                )
            elif area.area == "governance":
                steps.append(
                    "Assign ESG accountability and hold a 30-minute monthly review."
                )
            elif area.area == "data_foundation":
                steps.append(
                    "Standardize one shared ESG spreadsheet so updates are quick and repeatable."
                )
            elif area.area == "supply_chain":
                steps.append(
                    "Collect ESG declarations from top suppliers and flag high-risk gaps."
                )
        return steps

    def _build_plan_actions(self, themes: list[str]) -> list[ESGPlanAction]:
        action_map: dict[str, ESGPlanAction] = {
            "energy": ESGPlanAction(
                title="Build a monthly energy baseline",
                why_it_matters="Energy typically drives both emissions and operating cost for SMEs.",
                effort="low",
                timeline_weeks=2,
                owner="Operations lead",
                success_metric="Monthly kWh and fuel consumption recorded with no gaps.",
            ),
            "emissions": ESGPlanAction(
                title="Create first Scope 1 + 2 estimate",
                why_it_matters="Carbon visibility helps prioritize high-impact reduction areas.",
                effort="medium",
                timeline_weeks=3,
                owner="Finance or sustainability lead",
                success_metric="Baseline tCO2e estimate completed and reviewed.",
            ),
            "waste": ESGPlanAction(
                title="Launch waste stream tracking",
                why_it_matters="Waste segregation is often a low-cost, high-visibility ESG improvement.",
                effort="low",
                timeline_weeks=2,
                owner="Facilities manager",
                success_metric="Landfill and recycling quantities reported monthly.",
            ),
            "workforce": ESGPlanAction(
                title="Implement monthly workforce ESG check",
                why_it_matters="Workforce metrics improve retention, safety, and social reporting quality.",
                effort="low",
                timeline_weeks=2,
                owner="HR lead",
                success_metric="Monthly pulse completion rate above 80%.",
            ),
            "governance": ESGPlanAction(
                title="Formalize ESG ownership and cadence",
                why_it_matters="Governance sustains delivery and avoids ESG work stalling.",
                effort="low",
                timeline_weeks=1,
                owner="Leadership sponsor",
                success_metric="Named owner and recurring monthly ESG review established.",
            ),
            "data_foundation": ESGPlanAction(
                title="Standardize ESG data collection template",
                why_it_matters="A simple structure prevents rework and enables faster monthly updates.",
                effort="low",
                timeline_weeks=1,
                owner="Data coordinator",
                success_metric="Core ESG fields maintained in one shared template.",
            ),
            "supply_chain": ESGPlanAction(
                title="Assess top supplier ESG readiness",
                why_it_matters="Supplier issues can become customer or compliance risks.",
                effort="medium",
                timeline_weeks=4,
                owner="Procurement lead",
                success_metric="Top-10 suppliers profiled with ESG risk flags.",
            ),
        }

        actions: list[ESGPlanAction] = []
        for theme in themes:
            action = action_map.get(theme)
            if action:
                actions.append(action)
            if len(actions) >= 5:
                break

        if not actions:
            actions.append(action_map["data_foundation"])

        return actions

    async def _extract_metrics_with_ai(
        self,
        file_parts: list[types.Part],
        upload_records: list[UploadedFileRecord],
        text_preview: str | None = None,
    ) -> AIFileExtractionResult:
        if self.ai is None:
            return self._fallback_file_extraction(upload_records, text_preview)

        try:
            response = await self.ai.models.generate_content(
                model="gemini-2.5-flash",
                contents=file_parts,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=AIFileExtractionResult,
                ),
            )
            if response.parsed:
                return response.parsed
        except Exception:
            pass

        return self._fallback_file_extraction(upload_records, text_preview)

    def _fallback_file_extraction(
        self,
        upload_records: list[UploadedFileRecord],
        text_preview: str | None = None,
    ) -> AIFileExtractionResult:
        metrics: list[ExtractedMetric] = []

        if text_preview:
            inferred_metrics = self._extract_metrics_from_text_preview(text_preview)
            metrics.extend(inferred_metrics)

        for record in upload_records:
            filename = record.filename.lower()
            if "invoice" in filename:
                metrics.append(
                    ExtractedMetric(
                        metric_name="invoice_detected",
                        value="yes",
                        category="cost",
                        confidence=0.6,
                        evidence=f"Invoice-like filename detected: {record.filename}",
                    )
                )
            if (
                filename.endswith(".xlsx")
                or filename.endswith(".xls")
                or "sheet" in filename
            ):
                metrics.append(
                    ExtractedMetric(
                        metric_name="spreadsheet_uploaded",
                        value="yes",
                        category="data_foundation",
                        confidence=0.7,
                        evidence=f"Spreadsheet uploaded: {record.filename}",
                    )
                )
            if filename.endswith(".pdf"):
                metrics.append(
                    ExtractedMetric(
                        metric_name="document_uploaded",
                        value=record.filename,
                        category="document",
                        confidence=0.9,
                        evidence="PDF uploaded and available for review.",
                    )
                )

        if not metrics:
            metrics.append(
                ExtractedMetric(
                    metric_name="files_received",
                    value=str(len(upload_records)),
                    category="data_foundation",
                    confidence=0.9,
                    evidence="Files were uploaded successfully but automatic extraction was limited.",
                )
            )

        return AIFileExtractionResult(
            summary=(
                "Files were uploaded successfully. "
                "We extracted what we could from the provided file content; please review and refine if needed."
            ),
            metrics=metrics,
            follow_up_questions=[
                "Which month or reporting period do these files represent?",
                "Do you want extraction to prioritize energy, emissions, workforce, or waste metrics?",
            ],
        )

    def _extract_spreadsheet_preview(self, binary: bytes) -> str:
        values: list[str] = []

        # Prefer openpyxl when available for better spreadsheet value extraction.
        try:
            import openpyxl  # type: ignore

            workbook = openpyxl.load_workbook(
                io.BytesIO(binary),
                data_only=True,
                read_only=True,
            )
            for sheet in workbook.worksheets[:3]:
                for row in sheet.iter_rows(min_row=1, max_row=100, max_col=20):
                    row_values: list[str] = []
                    for cell in row:
                        if cell.value is None:
                            continue
                        text = str(cell.value).strip()
                        if text:
                            row_values.append(text)
                    if row_values:
                        values.append(" | ".join(row_values))
                    if len(values) >= 500:
                        break
                if len(values) >= 500:
                    break
            if values:
                return "\n".join(values)[:40000]
        except Exception:
            pass

        # Fallback parser for XLSX files without external dependencies.
        try:
            with zipfile.ZipFile(io.BytesIO(binary)) as archive:
                shared_strings: list[str] = []
                if "xl/sharedStrings.xml" in archive.namelist():
                    raw = archive.read("xl/sharedStrings.xml")
                    root = ET.fromstring(raw)
                    for item in root.findall(".//{*}si"):
                        parts = [node.text or "" for node in item.findall(".//{*}t")]
                        shared_strings.append("".join(parts).strip())

                sheet_names = [
                    name
                    for name in archive.namelist()
                    if name.startswith("xl/worksheets/sheet") and name.endswith(".xml")
                ]
                for sheet_name in sheet_names[:3]:
                    raw_sheet = archive.read(sheet_name)
                    root = ET.fromstring(raw_sheet)
                    for row in root.findall(".//{*}row"):
                        row_values: list[str] = []
                        for cell in row.findall("{*}c"):
                            cell_type = cell.attrib.get("t")
                            value_text = ""

                            value_node = cell.find("{*}v")
                            inline_node = cell.find("{*}is/{*}t")

                            if inline_node is not None and inline_node.text:
                                value_text = inline_node.text.strip()
                            elif value_node is not None and value_node.text:
                                value_text = value_node.text.strip()

                            if not value_text:
                                continue

                            if cell_type == "s":
                                try:
                                    idx = int(value_text)
                                    if 0 <= idx < len(shared_strings):
                                        value_text = shared_strings[idx]
                                except ValueError:
                                    pass

                            if value_text:
                                row_values.append(value_text)

                        if row_values:
                            values.append(" | ".join(row_values))

                        if len(values) >= 500:
                            break
                    if len(values) >= 500:
                        break
        except Exception:
            return ""

        return "\n".join(value for value in values if value)[:40000]

    def _normalize_media_type(self, upload: UploadFile) -> str:
        if upload.content_type:
            return upload.content_type.lower()

        suffix = Path(upload.filename or "").suffix.lower()
        mapping = {
            ".pdf": "application/pdf",
            ".csv": "text/csv",
            ".txt": "text/plain",
            ".xls": "application/vnd.ms-excel",
            ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            ".png": "image/png",
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".webp": "image/webp",
        }
        return mapping.get(suffix, "application/octet-stream")

    def _is_supported_upload(self, filename: str, media_type: str) -> bool:
        if media_type in self.SUPPORTED_MEDIA_TYPES:
            return True
        return Path(filename).suffix.lower() in {
            ".pdf",
            ".csv",
            ".txt",
            ".xls",
            ".xlsx",
            ".png",
            ".jpg",
            ".jpeg",
            ".webp",
        }

    async def _safe_ai_summary(
        self,
        prompt: str,
        fallback: str,
        max_sentences: int | None = None,
    ) -> str:
        if self.ai is None:
            return self._sanitize_ai_text(fallback, max_sentences=max_sentences)

        try:
            response = await self.ai.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt,
            )
            text = getattr(response, "text", None)
            if text and text.strip():
                return self._sanitize_ai_text(text, max_sentences=max_sentences)
        except Exception:
            pass
        return self._sanitize_ai_text(fallback, max_sentences=max_sentences)

    @staticmethod
    def _sanitize_ai_text(text: str, max_sentences: int | None = None) -> str:
        normalized = text.replace("\r\n", "\n").replace("\r", "\n")
        normalized = normalized.replace("```", "")
        normalized = normalized.replace("`", "")
        normalized = normalized.replace("**", "")
        normalized = normalized.replace("__", "")

        cleaned_lines: list[str] = []
        for line in normalized.split("\n"):
            stripped = line.strip()
            if not stripped:
                continue
            stripped = re.sub(r"^\s*(#{1,6}\s*|[-*•]\s*)", "", stripped)
            stripped = re.sub(r"^\s*\d+[\).]\s*", "", stripped)
            stripped = re.sub(r"\s{2,}", " ", stripped).strip()
            if stripped:
                cleaned_lines.append(stripped)

        cleaned = "\n".join(cleaned_lines).strip()
        if not cleaned:
            return ""

        if max_sentences is not None and max_sentences > 0:
            sentences = re.split(r"(?<=[.!?])\s+", cleaned)
            trimmed = [sentence.strip() for sentence in sentences if sentence.strip()]
            if trimmed:
                cleaned = " ".join(trimmed[:max_sentences])

        return cleaned

    def _validate_month(self, month: str) -> None:
        try:
            datetime.strptime(month, "%Y-%m")
        except ValueError as exc:
            raise HTTPException(
                status_code=422, detail="Month must be in YYYY-MM format."
            ) from exc

    def _refresh_focus_from_changes(
        self,
        existing_focus: list[dict[str, Any]],
        changes: dict[str, Any],
    ) -> list[FocusArea]:
        if not existing_focus:
            return [
                FocusArea(
                    area="data_foundation",
                    priority="high",
                    reason="No prior focus areas found. Rebuild monthly baseline first.",
                )
            ]

        priority_score: dict[FocusPriority, int] = {"low": 1, "medium": 2, "high": 3}
        updated_scores: dict[FocusAreaName, int] = {}
        reasons: dict[FocusAreaName, str] = {}

        for item in existing_focus:
            area = self._parse_focus_area(item.get("area"))
            if area is None:
                continue
            current_priority = self._parse_priority(item.get("priority"))
            updated_scores[area] = priority_score.get(current_priority, 2)
            reasons[area] = item.get("reason", "")

        energy_change = self._to_float(changes.get("energy_change_pct"))
        waste_change = self._to_float(changes.get("waste_change_pct"))

        if energy_change is not None and energy_change > 5:
            updated_scores["energy"] = updated_scores.get("energy", 1) + 1
            reasons["energy"] = (
                "Energy use increased this month and should be reviewed quickly."
            )
        if waste_change is not None and waste_change > 5:
            updated_scores["waste"] = updated_scores.get("waste", 1) + 1
            reasons["waste"] = (
                "Waste volume increased this month and needs corrective action."
            )

        if str(changes.get("fuel_or_logistics_change", "")).lower() == "increased":
            updated_scores["emissions"] = updated_scores.get("emissions", 1) + 1
            reasons["emissions"] = (
                "Fuel/logistics activity increased and may raise emissions."
            )

        ranked = sorted(updated_scores.items(), key=lambda item: item[1], reverse=True)
        refreshed: list[FocusArea] = []

        for area, score in ranked[:4]:
            priority: FocusPriority
            if score >= 4:
                priority = "high"
            elif score >= 2:
                priority = "medium"
            else:
                priority = "low"

            refreshed.append(
                FocusArea(
                    area=area,
                    priority=priority,
                    reason=reasons.get(area, "Updated from monthly changes."),
                )
            )

        return refreshed

    @staticmethod
    def _parse_focus_area(value: Any) -> FocusAreaName | None:
        if not isinstance(value, str):
            return None
        normalized = value.strip().lower()
        if normalized in {
            "energy",
            "emissions",
            "waste",
            "workforce",
            "governance",
            "data_foundation",
            "supply_chain",
        }:
            return cast(FocusAreaName, normalized)
        return None

    @staticmethod
    def _parse_priority(value: Any) -> FocusPriority:
        if isinstance(value, str):
            normalized = value.strip().lower()
            if normalized in {"low", "medium", "high"}:
                return cast(FocusPriority, normalized)
        return "medium"

    def _next_actions_from_changes(self, changes: dict[str, Any]) -> list[str]:
        actions = []

        energy_change = self._to_float(changes.get("energy_change_pct"))
        if energy_change is not None and energy_change > 0:
            actions.append(
                "Investigate top energy-consuming equipment and schedule efficiency checks."
            )

        waste_change = self._to_float(changes.get("waste_change_pct"))
        if waste_change is not None and waste_change > 0:
            actions.append(
                "Audit waste segregation process and reduce landfill stream leakage."
            )

        if str(changes.get("fuel_or_logistics_change", "")).lower() == "increased":
            actions.append(
                "Review routing/transport utilization to reduce fuel intensity."
            )

        major_action = str(changes.get("major_esg_action", "")).strip()
        if not major_action:
            actions.append(
                "Complete one measurable ESG action before next monthly update."
            )

        if not actions:
            actions.append("Maintain current ESG cadence and continue monthly updates.")

        return actions[:3]

    def _build_quick_wins(self, focus_areas: Sequence[str]) -> list[QuickWinItem]:
        suggestions_by_area = {
            "energy": QuickWinItem(
                title="Track energy from last 3 utility bills",
                impact_area="energy",
                effort="low",
                expected_benefit="Find immediate savings opportunities and establish baseline usage.",
                why_recommended="Energy tracking is usually the fastest way for SMEs to see measurable ESG progress.",
                first_step="Create one monthly sheet with kWh and cost by facility.",
                estimated_cost_savings_php=18000,
            ),
            "emissions": QuickWinItem(
                title="Estimate Scope 1 + 2 using existing bills",
                impact_area="emissions",
                effort="low",
                expected_benefit="Create your first carbon snapshot without complex tooling.",
                why_recommended="You already have enough data from fuel and electricity documents.",
                first_step="Map electricity and fuel totals to a simple emissions calculator.",
                estimated_cost_savings_php=12000,
            ),
            "waste": QuickWinItem(
                title="Run a one-week waste separation trial",
                impact_area="waste",
                effort="low",
                expected_benefit="Cut landfill waste quickly and improve recycling rates.",
                why_recommended="Small process changes often deliver visible waste improvements in under a month.",
                first_step="Label waste streams and record weekly weights by category.",
                estimated_cost_savings_php=9000,
            ),
            "workforce": QuickWinItem(
                title="Start a monthly workforce wellbeing pulse",
                impact_area="workforce",
                effort="low",
                expected_benefit="Spot retention and safety risks early with lightweight tracking.",
                why_recommended="People metrics are often under-tracked but highly impactful for ESG maturity.",
                first_step="Use a 5-question anonymous survey and monitor trend lines.",
                estimated_cost_savings_php=7000,
            ),
            "governance": QuickWinItem(
                title="Assign ESG ownership and a 30-minute monthly review",
                impact_area="governance",
                effort="low",
                expected_benefit="Turns ESG from ad-hoc efforts into repeatable execution.",
                why_recommended="Clear ownership is the single biggest predictor of sustained progress.",
                first_step="Nominate one owner and create a recurring review meeting.",
                estimated_cost_savings_php=6000,
            ),
            "data_foundation": QuickWinItem(
                title="Build one shared ESG data template",
                impact_area="data_foundation",
                effort="low",
                expected_benefit="Avoid rework and make monthly updates take minutes, not hours.",
                why_recommended="A clean data template removes the biggest SME ESG bottleneck.",
                first_step="Define core fields for energy, emissions, waste, and headcount.",
                estimated_cost_savings_php=15000,
            ),
            "supply_chain": QuickWinItem(
                title="Collect top-5 supplier sustainability details",
                impact_area="supply_chain",
                effort="medium",
                expected_benefit="Improve procurement risk visibility and customer trust.",
                why_recommended="Most SMEs can start supply chain ESG with a small supplier subset.",
                first_step="Request environmental and labor policy docs from your largest suppliers.",
                estimated_cost_savings_php=11000,
            ),
        }

        quick_wins: list[QuickWinItem] = []
        for area in focus_areas:
            item = suggestions_by_area.get(area)
            if item and item.title not in {win.title for win in quick_wins}:
                quick_wins.append(item)
            if len(quick_wins) >= 5:
                break

        if not quick_wins:
            quick_wins.append(suggestions_by_area["data_foundation"])

        return quick_wins

    def _infer_disclosure_tag(self, filename: str, notes: str | None) -> str:
        normalized = f"{filename} {notes or ''}".lower()
        if any(token in normalized for token in ["waste", "segregation", "landfill"]):
            return "306-3"
        if any(token in normalized for token in ["diesel", "fuel", "fleet"]):
            return "305-1"
        if any(
            token in normalized for token in ["electric", "kwh", "utility", "power"]
        ):
            return "302-1"
        if any(
            token in normalized
            for token in ["hire", "turnover", "headcount", "hr", "payroll"]
        ):
            return "401-1"
        return "302-1"

    def _save_evidence_bytes(self, company_id: str, file_id: str, binary: bytes) -> str:
        company_dir = self.evidence_root / company_id / "evidence"
        company_dir.mkdir(parents=True, exist_ok=True)
        file_path = company_dir / file_id
        file_path.write_bytes(binary)
        return str(file_path)

    async def _extract_fixed_metrics_with_ai(
        self,
        file_parts: list[types.Part],
        fallback_headcount: Any,
        text_preview: str | None = None,
    ) -> FixedExtractionMetrics:
        heuristic_metrics = self._fixed_metrics_from_text_preview(
            text_preview=text_preview,
            fallback_headcount=fallback_headcount,
        )

        if self.ai is None:
            logger.info(
                "AI client unavailable for fixed extraction. Using heuristic fallback."
            )
            return heuristic_metrics

        extraction_prompt = (
            "Extract ESG values using this exact JSON schema only: "
            "electricity_kwh, diesel_liters, waste_kg, headcount, new_hires, turnover_count, missing_fields. "
            "If a value is absent, return null and include its field name in missing_fields. "
            "Do not add extra keys."
        )
        structured_parts = [types.Part.from_text(text=extraction_prompt)]
        if len(file_parts) > 1:
            structured_parts.extend(file_parts[1:])

        try:
            response = await self.ai.models.generate_content(
                model="gemini-2.5-flash",
                contents=structured_parts,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=FixedExtractionMetrics,
                ),
            )
            if response.parsed:
                logger.info("AI fixed extraction parsed successfully.")
                return self._merge_fixed_metrics(
                    primary=self._ensure_fixed_missing_fields(response.parsed),
                    fallback=heuristic_metrics,
                )
        except Exception:
            logger.exception("AI fixed extraction failed; using heuristic fallback.")
            pass

        logger.info(
            "AI fixed extraction returned no parsed payload; using heuristic fallback."
        )
        return heuristic_metrics

    def _merge_fixed_metrics(
        self,
        primary: FixedExtractionMetrics,
        fallback: FixedExtractionMetrics,
    ) -> FixedExtractionMetrics:
        merged = FixedExtractionMetrics(
            electricity_kwh=(
                primary.electricity_kwh
                if primary.electricity_kwh is not None
                else fallback.electricity_kwh
            ),
            diesel_liters=(
                primary.diesel_liters
                if primary.diesel_liters is not None
                else fallback.diesel_liters
            ),
            waste_kg=(
                primary.waste_kg if primary.waste_kg is not None else fallback.waste_kg
            ),
            headcount=(
                primary.headcount
                if primary.headcount is not None
                else fallback.headcount
            ),
            new_hires=(
                primary.new_hires
                if primary.new_hires is not None
                else fallback.new_hires
            ),
            turnover_count=(
                primary.turnover_count
                if primary.turnover_count is not None
                else fallback.turnover_count
            ),
        )
        return self._ensure_fixed_missing_fields(merged)

    def _extract_metrics_from_text_preview(
        self,
        text_preview: str,
    ) -> list[ExtractedMetric]:
        fixed = self._fixed_metrics_from_text_preview(
            text_preview=text_preview,
            fallback_headcount=None,
        )
        metrics: list[ExtractedMetric] = []

        mapping: list[tuple[str, float | int | None, str, str]] = [
            ("electricity_kwh", fixed.electricity_kwh, "kWh", "energy"),
            ("diesel_liters", fixed.diesel_liters, "liters", "energy"),
            ("waste_kg", fixed.waste_kg, "kg", "waste"),
            ("headcount", fixed.headcount, "employees", "workforce"),
            ("new_hires", fixed.new_hires, "employees", "workforce"),
            ("turnover_count", fixed.turnover_count, "employees", "workforce"),
        ]

        for metric_name, value, unit, category in mapping:
            if value is None:
                continue
            metrics.append(
                ExtractedMetric(
                    metric_name=metric_name,
                    value=str(value),
                    unit=unit,
                    category=category,
                    confidence=0.65,
                    evidence="Inferred from uploaded spreadsheet/text content.",
                )
            )

        return metrics

    def _extract_numeric_after_keywords(
        self,
        text: str,
        keywords: list[str],
    ) -> float | None:
        lowered = text.lower()
        pattern = re.compile(r"(-?\d{1,3}(?:,\d{3})*(?:\.\d+)?|-?\d+(?:\.\d+)?)")
        candidates: list[float] = []

        # First pass: line-scoped matching preserves spreadsheet row structure.
        for line in text.splitlines():
            line_lower = line.lower()
            if not any(keyword in line_lower for keyword in keywords):
                continue
            for match in pattern.finditer(line):
                number_text = match.group(1).replace(",", "")
                try:
                    value = float(number_text)
                except ValueError:
                    continue
                if value > 0:
                    candidates.append(value)

        for keyword in keywords:
            search_start = 0
            while True:
                idx = lowered.find(keyword, search_start)
                if idx == -1:
                    break
                search_start = idx + len(keyword)

                # Capture numbers both before and after the keyword.
                left = max(0, idx - 120)
                right = min(len(text), idx + len(keyword) + 120)
                window = text[left:right]

                for match in pattern.finditer(window):
                    number_text = match.group(1).replace(",", "")
                    try:
                        value = float(number_text)
                    except ValueError:
                        continue
                    if value > 0:
                        candidates.append(value)

        if not candidates:
            return None

        # Prefer the largest positive value as a practical default for ESG totals.
        return max(candidates)

    def _fixed_metrics_from_text_preview(
        self,
        text_preview: str | None,
        fallback_headcount: Any,
    ) -> FixedExtractionMetrics:
        if not text_preview:
            return self._fixed_metrics_from_changes({}, fallback_headcount)

        electricity_kwh = self._extract_numeric_after_keywords(
            text_preview,
            ["electricity", "kwh", "power consumption", "grid"],
        )
        diesel_liters = self._extract_numeric_after_keywords(
            text_preview,
            ["diesel", "fuel liters", "fuel usage", "liters"],
        )
        waste_kg = self._extract_numeric_after_keywords(
            text_preview,
            ["waste", "landfill", "recycled", "kg"],
        )
        headcount = self._extract_numeric_after_keywords(
            text_preview,
            ["headcount", "employees", "employee count", "workforce"],
        )
        new_hires = self._extract_numeric_after_keywords(
            text_preview,
            ["new hires", "hires", "hired"],
        )
        turnover_count = self._extract_numeric_after_keywords(
            text_preview,
            ["turnover", "attrition", "leavers"],
        )

        parsed_headcount = self._to_int(headcount)
        if parsed_headcount is None:
            parsed_headcount = self._to_int(fallback_headcount)

        metrics = FixedExtractionMetrics(
            electricity_kwh=electricity_kwh,
            diesel_liters=diesel_liters,
            waste_kg=waste_kg,
            headcount=parsed_headcount,
            new_hires=self._to_int(new_hires),
            turnover_count=self._to_int(turnover_count),
        )
        return self._ensure_fixed_missing_fields(metrics)

    def _ensure_fixed_missing_fields(
        self,
        metrics: FixedExtractionMetrics,
    ) -> FixedExtractionMetrics:
        fields = [
            "electricity_kwh",
            "diesel_liters",
            "waste_kg",
            "headcount",
            "new_hires",
            "turnover_count",
        ]
        missing_fields = [field for field in fields if getattr(metrics, field) is None]
        return metrics.model_copy(update={"missing_fields": missing_fields})

    def _fixed_metrics_from_changes(
        self,
        changes: dict[str, Any],
        fallback_headcount: Any,
    ) -> FixedExtractionMetrics:
        electricity_kwh = self._extract_first_numeric(
            changes,
            ["electricity_kwh", "kwh", "energy_kwh"],
        )
        diesel_liters = self._extract_first_numeric(
            changes,
            ["diesel_liters", "fuel_liters", "fuel_usage_liters"],
        )
        waste_kg = self._extract_first_numeric(
            changes,
            ["waste_kg", "waste_generated_kg", "landfill_waste_kg"],
        )

        headcount_value = self._extract_first_numeric(
            changes,
            ["headcount", "employee_count", "employees"],
        )
        if headcount_value is None:
            headcount_value = self._to_float(fallback_headcount)

        new_hires = self._extract_first_numeric(
            changes,
            ["new_hires", "hires_count", "new_hires_count"],
        )
        turnover_count = self._extract_first_numeric(
            changes,
            ["turnover_count", "employee_turnover", "leavers_count"],
        )

        metrics = FixedExtractionMetrics(
            electricity_kwh=electricity_kwh,
            diesel_liters=diesel_liters,
            waste_kg=waste_kg,
            headcount=self._to_int(headcount_value),
            new_hires=self._to_int(new_hires),
            turnover_count=self._to_int(turnover_count),
        )
        return self._ensure_fixed_missing_fields(metrics)

    def _extract_first_numeric(
        self,
        payload: dict[str, Any],
        keys: list[str],
    ) -> float | None:
        for key in keys:
            if key in payload:
                value = self._to_float(payload.get(key))
                if value is not None:
                    return value
        return None

    def _run_submission_pipeline(
        self,
        company_id: str,
        company_data: dict[str, Any],
        fixed_extraction: FixedExtractionMetrics,
        source: str,
        month: str | None,
        changes: dict[str, Any] | None,
        notes: str | None,
        evidence_records: list[dict[str, Any]],
    ) -> dict[str, Any]:
        base_year = month[:4] if month else str(datetime.now(timezone.utc).year)

        gri_302, gri_305, gri_401 = self._map_fixed_metrics_to_gri_models(
            fixed_extraction=fixed_extraction,
            company_data=company_data,
            base_year=base_year,
        )

        computations = {
            "gri_302": self.GRI302Engine.run(gri_302),
            "gri_305": self.GRI305Engine.run(gri_305),
            "gri_401": self.GRI401Engine.run(gri_401),
        }

        submission_id = str(uuid4())
        report_payload = self._build_report_from_results(
            company_id=company_id,
            submission_id=submission_id,
            fixed_extraction=fixed_extraction,
            computations=computations,
        )
        dashboard_payload = self._build_dashboard_from_results(
            fixed_extraction=fixed_extraction,
            computations=computations,
        )
        serialized_computations = jsonable_encoder(computations)

        submission_payload = {
            "submission_id": submission_id,
            "source": source,
            "month": month,
            "notes": notes,
            "changes": changes or {},
            "fixed_extraction": fixed_extraction.model_dump(mode="json"),
            "gri_models": {
                "gri_302": gri_302.model_dump(mode="json"),
                "gri_305": gri_305.model_dump(mode="json"),
                "gri_401": gri_401.model_dump(mode="json"),
            },
            "computations": serialized_computations,
            "dashboard": dashboard_payload,
            "report": report_payload,
            "evidence": evidence_records,
            "submitted_at": self._utc_now_iso(),
        }

        self.repo.save_submission(company_id, submission_payload)
        self.repo.save_latest_dashboard(company_id, dashboard_payload)
        self.repo.save_latest_report(company_id, report_payload)

        return submission_payload

    def _map_fixed_metrics_to_gri_models(
        self,
        fixed_extraction: FixedExtractionMetrics,
        company_data: dict[str, Any],
        base_year: str,
    ) -> tuple[AIExtracted_GRI_302, AIExtracted_GRI_305, AIExtracted_GRI_401]:
        profile = company_data.get("profile", {})
        headcount = fixed_extraction.headcount
        if headcount is None:
            headcount = self._to_int(profile.get("employee_count"))
        revenue = self._to_float(profile.get("annual_revenue"))

        energy_entries: list[EnergyEntry] = []
        if fixed_extraction.electricity_kwh is not None:
            energy_entries.append(
                EnergyEntry(
                    energy_type="electricity",
                    value=fixed_extraction.electricity_kwh,
                    unit="kWh",
                    converted_mj=round(fixed_extraction.electricity_kwh * 3.6, 3),
                    is_renewable=False,
                    source="grid electricity",
                    confidence=0.85,
                )
            )
        if fixed_extraction.diesel_liters is not None:
            energy_entries.append(
                EnergyEntry(
                    energy_type="diesel",
                    value=fixed_extraction.diesel_liters,
                    unit="liters",
                    converted_mj=round(fixed_extraction.diesel_liters * 36.54, 3),
                    is_renewable=False,
                    source="diesel fuel",
                    confidence=0.85,
                )
            )

        total_energy_mj = (
            round(sum(item.converted_mj for item in energy_entries), 3)
            if energy_entries
            else None
        )
        external_energy_mj = (
            round(fixed_extraction.electricity_kwh * 3.6, 3)
            if fixed_extraction.electricity_kwh is not None
            else None
        )
        intensity_denominator = (
            "per_employee"
            if headcount is not None
            else ("per_revenue_unit" if revenue is not None else None)
        )

        omissions_302: list[Omission302] = []
        if not energy_entries:
            omissions_302.append(
                Omission302(
                    field_name="energy_entries",
                    reason="No electricity_kwh or diesel_liters values were extracted.",
                )
            )
        if total_energy_mj is None:
            omissions_302.append(
                Omission302(
                    field_name="total_energy_mj",
                    reason="Unable to compute total energy without extracted energy entries.",
                )
            )
        if headcount is None and revenue is None:
            omissions_302.append(
                Omission302(
                    field_name="employee_count",
                    reason="No headcount is available for energy intensity calculations.",
                )
            )

        extracted_302 = AIExtracted_GRI_302(
            energy_entries=energy_entries or None,
            total_energy_mj=total_energy_mj,
            renewable_energy_mj=0.0 if energy_entries else None,
            non_renewable_energy_mj=total_energy_mj,
            external_energy_mj=external_energy_mj,
            employee_count=headcount,
            revenue=revenue,
            intensity_denominator=intensity_denominator,
            energy_reduction_mj=None,
            baseline_year=None,
            product_energy_reduction_mj=None,
            conversion_factors=ConversionFactors(),
            base_year=base_year,
            omitted_fields=omissions_302,
        )

        scope1_entries: list[EmissionEntry] = []
        if fixed_extraction.diesel_liters is not None:
            diesel_kg = round(fixed_extraction.diesel_liters * 2.68, 3)
            scope1_entries.append(
                EmissionEntry(
                    source="diesel combustion",
                    fuel_or_activity="diesel",
                    quantity=fixed_extraction.diesel_liters,
                    unit="liters",
                    emission_factor=2.68,
                    emission_factor_unit="kg CO2e/liter",
                    emissions_kg_co2e=diesel_kg,
                    ghg_gases_included=["CO2", "CH4", "N2O"],
                    is_biogenic=False,
                    confidence=0.85,
                )
            )

        scope2_entries: list[EmissionEntry] = []
        if fixed_extraction.electricity_kwh is not None:
            electricity_kg = round(fixed_extraction.electricity_kwh * 0.55, 3)
            scope2_entries.append(
                EmissionEntry(
                    source="grid electricity",
                    fuel_or_activity="electricity",
                    quantity=fixed_extraction.electricity_kwh,
                    unit="kWh",
                    emission_factor=0.55,
                    emission_factor_unit="kg CO2e/kWh",
                    emissions_kg_co2e=electricity_kg,
                    ghg_gases_included=["CO2"],
                    is_biogenic=False,
                    confidence=0.85,
                )
            )

        scope1_total = (
            round(sum(entry.emissions_kg_co2e for entry in scope1_entries), 3)
            if scope1_entries
            else None
        )
        scope2_total = (
            round(sum(entry.emissions_kg_co2e for entry in scope2_entries), 3)
            if scope2_entries
            else None
        )
        scope3_total = (
            round(fixed_extraction.waste_kg * 1.9, 3)
            if fixed_extraction.waste_kg is not None
            else None
        )

        omissions_305: list[Omission305] = []
        if not scope1_entries:
            omissions_305.append(
                Omission305(
                    field_name="scope1_entries",
                    reason="No diesel or direct fuel activity data was extracted.",
                )
            )
        if not scope2_entries:
            omissions_305.append(
                Omission305(
                    field_name="scope2_entries",
                    reason="No electricity_kwh value was extracted for Scope 2.",
                )
            )
        if scope3_total is None:
            omissions_305.append(
                Omission305(
                    field_name="scope3_total_kg_co2e",
                    reason="No waste_kg value was extracted for a Scope 3 proxy.",
                )
            )

        extracted_305 = AIExtracted_GRI_305(
            scope1_entries=scope1_entries or None,
            scope1_total_kg_co2e=scope1_total,
            scope1_biogenic_kg_co2=0.0 if scope1_total is not None else None,
            scope2_entries=scope2_entries or None,
            scope2_location_based_kg_co2e=scope2_total,
            scope2_market_based_kg_co2e=None,
            scope2_biogenic_kg_co2=0.0 if scope2_total is not None else None,
            scope3_total_kg_co2e=scope3_total,
            scope3_categories_included=(
                ["waste_generated_in_operations"] if scope3_total is not None else None
            ),
            scope3_biogenic_kg_co2=None,
            employee_count=headcount,
            revenue=revenue,
            intensity_denominator=intensity_denominator,
            intensity_scopes_included=(
                ["scope1", "scope2"] if scope1_total or scope2_total else None
            ),
            ghg_reduction_kg_co2e=None,
            reduction_scopes_included=None,
            baseline_year=None,
            ods_kg_cfc11e=None,
            ods_substances=None,
            nox_kg=None,
            sox_kg=None,
            voc_kg=None,
            pm_kg=None,
            emission_factor_metadata=EmissionFactorMetadata(
                source="IPCC Default Emission Factors 2006",
                calculation_methodology="location-based",
            ),
            base_year=base_year,
            omitted_fields=omissions_305,
        )

        omissions_401: list[Omission401] = []
        if fixed_extraction.new_hires is None:
            omissions_401.append(
                Omission401(
                    field_name="total_new_hires",
                    reason="New hire count is not available in current submission data.",
                )
            )
        if fixed_extraction.turnover_count is None:
            omissions_401.append(
                Omission401(
                    field_name="total_turnover",
                    reason="Turnover count is not available in current submission data.",
                )
            )
        if headcount is None:
            omissions_401.append(
                Omission401(
                    field_name="new_hire_rate",
                    reason="Headcount metadata is missing for workforce rate calculations.",
                )
            )

        new_hire_rate = None
        turnover_rate = None
        if headcount and headcount > 0:
            if fixed_extraction.new_hires is not None:
                new_hire_rate = round((fixed_extraction.new_hires / headcount) * 100, 2)
            if fixed_extraction.turnover_count is not None:
                turnover_rate = round(
                    (fixed_extraction.turnover_count / headcount) * 100, 2
                )

        extracted_401 = AIExtracted_GRI_401(
            total_new_hires=fixed_extraction.new_hires,
            new_hire_rate=new_hire_rate,
            new_hires_by_gender=None,
            new_hires_by_age_group=None,
            new_hires_by_region=None,
            total_turnover=fixed_extraction.turnover_count,
            turnover_rate=turnover_rate,
            turnover_by_gender=None,
            turnover_by_age_group=None,
            turnover_by_region=None,
            benefits=None,
            significant_location=profile.get("location"),
            parental_leave_by_gender=None,
            return_to_work_rate_by_gender=None,
            retention_rate_by_gender=None,
            employee_count=headcount,
            base_year=base_year,
            omitted_fields=omissions_401,
        )

        return extracted_302, extracted_305, extracted_401

    def _build_dashboard_from_results(
        self,
        fixed_extraction: FixedExtractionMetrics,
        computations: dict[str, Any],
    ) -> dict[str, Any]:
        summaries = [
            computations.get("gri_302", {}).get("summary", {}),
            computations.get("gri_305", {}).get("summary", {}),
            computations.get("gri_401", {}).get("summary", {}),
        ]
        total_count = sum(int(item.get("total_count", 0)) for item in summaries)
        computed_count = sum(int(item.get("computed_count", 0)) for item in summaries)
        coverage = (computed_count / total_count) if total_count > 0 else 0.0

        esg_score = round(min(100.0, coverage * 100), 1)
        compliance_status = "On Track" if coverage >= 0.6 else "Needs Attention"

        kpis: list[DashboardKPI] = []

        total_energy_data = (
            computations.get("gri_302", {}).get("302_1", {}).get("value", {})
        )
        total_energy = (
            total_energy_data.get("total_energy_mj") if total_energy_data else None
        )
        if total_energy is not None:
            kpis.append(
                DashboardKPI(
                    name="Total Energy",
                    value=round(float(total_energy), 2),
                    unit="MJ",
                    rating=self._rate_kpi("energy", float(total_energy)),
                )
            )

        scope1_total_data = (
            (computations.get("gri_305") or {}).get("305_1") or {}
        ).get("value") or {}
        scope1_total = (
            scope1_total_data.get("total_kg_co2e") if scope1_total_data else None
        )
        if scope1_total is not None:
            kpis.append(
                DashboardKPI(
                    name="Scope 1 Emissions",
                    value=round(float(scope1_total), 2),
                    unit="kg CO2e",
                    rating=self._rate_kpi("emissions", float(scope1_total)),
                )
            )

        scope2_total_data = (
            (computations.get("gri_305") or {}).get("305_2") or {}
        ).get("value") or {}
        scope2_total = (
            scope2_total_data.get("location_based_kg_co2e")
            if scope2_total_data
            else None
        )
        if scope2_total is not None:
            kpis.append(
                DashboardKPI(
                    name="Scope 2 Emissions",
                    value=round(float(scope2_total), 2),
                    unit="kg CO2e",
                    rating=self._rate_kpi("emissions", float(scope2_total)),
                )
            )

        if fixed_extraction.waste_kg is not None:
            kpis.append(
                DashboardKPI(
                    name="Waste Generated",
                    value=round(float(fixed_extraction.waste_kg), 2),
                    unit="kg",
                    rating=self._rate_kpi("waste", float(fixed_extraction.waste_kg)),
                )
            )

        gri_401_1_value = ((computations.get("gri_401") or {}).get("401_1") or {}).get(
            "value"
        ) or {}
        hires_rate = (gri_401_1_value.get("new_hires") or {}).get("rate")
        if hires_rate is not None:
            kpis.append(
                DashboardKPI(
                    name="New Hire Rate",
                    value=round(float(hires_rate), 2),
                    unit="%",
                    rating=self._rate_kpi("new_hire_rate", float(hires_rate)),
                )
            )

        turnover_rate = (gri_401_1_value.get("turnover") or {}).get("rate")
        if turnover_rate is not None:
            kpis.append(
                DashboardKPI(
                    name="Turnover Rate",
                    value=round(float(turnover_rate), 2),
                    unit="%",
                    rating=self._rate_kpi("turnover_rate", float(turnover_rate)),
                )
            )

        if len(kpis) < 3:
            kpis.append(
                DashboardKPI(
                    name="GRI Coverage",
                    value=round(coverage * 100, 1),
                    unit="%",
                    rating=self._rate_kpi("coverage", coverage * 100),
                )
            )

        return {
            "esg_score": esg_score,
            "compliance_status": compliance_status,
            "kpis": [item.model_dump(mode="json") for item in kpis[:8]],
            "computed_count": computed_count,
            "total_count": total_count,
        }

    def _rate_kpi(self, kind: str, value: float) -> Literal["Good", "Better", "Best"]:
        if kind in {"energy", "emissions", "waste", "turnover_rate"}:
            if value <= 1000:
                return "Best"
            if value <= 5000:
                return "Better"
            return "Good"

        if kind == "new_hire_rate":
            if value >= 10:
                return "Best"
            if value >= 5:
                return "Better"
            return "Good"

        if kind == "coverage":
            if value >= 80:
                return "Best"
            if value >= 60:
                return "Better"
            return "Good"

        return "Better"

    def _build_report_from_results(
        self,
        company_id: str,
        submission_id: str,
        fixed_extraction: FixedExtractionMetrics,
        computations: dict[str, Any],
    ) -> dict[str, Any]:
        disclosures: list[ESGReportDisclosure] = []
        reasons_for_omission: list[OmissionReason] = []

        report_map = [
            (
                "302-1",
                "Energy consumption within the organization",
                computations.get("gri_302", {}).get("302_1", {}),
            ),
            (
                "302-3",
                "Energy intensity",
                computations.get("gri_302", {}).get("302_3", {}),
            ),
            (
                "305-1",
                "Direct (Scope 1) GHG emissions",
                computations.get("gri_305", {}).get("305_1", {}),
            ),
            (
                "305-2",
                "Energy indirect (Scope 2) GHG emissions",
                computations.get("gri_305", {}).get("305_2", {}),
            ),
            (
                "305-4",
                "GHG emissions intensity",
                computations.get("gri_305", {}).get("305_4", {}),
            ),
            (
                "401-1",
                "New employee hires and employee turnover",
                computations.get("gri_401", {}).get("401_1", {}),
            ),
        ]

        for disclosure_code, title, result in report_map:
            computed = bool(result.get("computed"))
            reason = result.get("reason")
            entry = ESGReportDisclosure(
                disclosure=disclosure_code,
                title=title,
                computed=computed,
                value=result.get("value"),
                unit=result.get("unit"),
                reason_for_omission=reason if not computed else None,
            )
            disclosures.append(entry)
            if not computed:
                reasons_for_omission.append(
                    OmissionReason(
                        disclosure=disclosure_code,
                        reason=reason or "Not enough data to compute this disclosure.",
                    )
                )

        if fixed_extraction.waste_kg is not None:
            disclosures.append(
                ESGReportDisclosure(
                    disclosure="306-3",
                    title="Waste generated",
                    computed=True,
                    value={"waste_generated_kg": round(fixed_extraction.waste_kg, 2)},
                    unit="kg",
                )
            )
            disclosures.append(
                ESGReportDisclosure(
                    disclosure="306-4",
                    title="Waste diverted from disposal",
                    computed=True,
                    value={
                        "waste_diverted_kg": round(fixed_extraction.waste_kg * 0.3, 2),
                        "assumed_diversion_ratio": 0.3,
                    },
                    unit="kg",
                )
            )
        else:
            disclosures.append(
                ESGReportDisclosure(
                    disclosure="306-3",
                    title="Waste generated",
                    computed=False,
                    value=None,
                    unit="kg",
                    reason_for_omission="Missing required field: waste_kg.",
                )
            )
            disclosures.append(
                ESGReportDisclosure(
                    disclosure="306-4",
                    title="Waste diverted from disposal",
                    computed=False,
                    value=None,
                    unit="kg",
                    reason_for_omission="Cannot compute without waste_kg baseline.",
                )
            )
            reasons_for_omission.append(
                OmissionReason(
                    disclosure="306-3",
                    reason="Missing required field: waste_kg.",
                )
            )
            reasons_for_omission.append(
                OmissionReason(
                    disclosure="306-4",
                    reason="Cannot compute without waste_kg baseline.",
                )
            )

        return ESGReportResponse(
            company_id=company_id,
            generated_at=datetime.now(timezone.utc),
            disclosures=disclosures,
            reasons_for_omission=reasons_for_omission,
            source_submission_id=submission_id,
        ).model_dump(mode="json")

    def _build_report_payload(
        self,
        company_id: str,
        submission_payload: dict[str, Any],
    ) -> dict[str, Any]:
        report = submission_payload.get("report")
        if isinstance(report, dict) and report.get("disclosures"):
            return report

        fixed_extraction = FixedExtractionMetrics.model_validate(
            submission_payload.get("fixed_extraction", {})
        )
        computations = submission_payload.get("computations", {})
        submission_id = str(submission_payload.get("submission_id", uuid4()))
        return self._build_report_from_results(
            company_id=company_id,
            submission_id=submission_id,
            fixed_extraction=fixed_extraction,
            computations=computations,
        )

    def _kpi_labels_from_submission(
        self,
        submission_payload: dict[str, Any] | None,
    ) -> list[str]:
        if not submission_payload:
            return []
        dashboard = submission_payload.get("dashboard", {})
        labels = []
        for item in dashboard.get("kpis", []):
            name = str(item.get("name", "")).strip()
            if name:
                labels.append(name)
        return labels

    async def _refresh_plan_from_latest_pipeline(
        self,
        company_id: str,
        company_data: dict[str, Any],
    ) -> dict[str, Any]:
        existing_plan = company_data.get("plan") or {}
        if not existing_plan:
            return {}

        latest_submission = self.repo.get_latest_submission(company_id)
        latest_report = self.repo.get_latest_report(company_id)
        kpis = self._kpi_labels_from_submission(latest_submission)
        ready_for_pdf = bool(latest_report and latest_report.get("disclosures"))

        summary = str(existing_plan.get("one_page_summary", "")).strip()
        if kpis:
            summary_prompt = (
                "Rewrite this ESG plan summary to include monthly update momentum and latest KPI focus areas. "
                "Return plain text only in 3-4 short sentences.\n"
                f"Current summary: {summary}\n"
                f"KPI focus: {kpis}"
            )
            summary = await self._safe_ai_summary(
                summary_prompt,
                fallback=summary,
                max_sentences=4,
            )

        refreshed_plan = {
            **existing_plan,
            "generated_at": self._utc_now_iso(),
            "one_page_summary": summary,
            "kpis": kpis,
            "ready_for_pdf": ready_for_pdf,
        }
        self.repo.save_plan(company_id, refreshed_plan)
        return refreshed_plan

    @staticmethod
    def _stringify_report_value(value: Any) -> str:
        if value is None:
            return ""
        if isinstance(value, (str, int, float, bool)):
            return str(value)
        return str(value)

    @staticmethod
    def _escape_pdf_text(value: str) -> str:
        return value.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")

    def _build_simple_pdf(self, lines: list[str]) -> bytes:
        text_lines = [self._escape_pdf_text(line[:120]) for line in lines[:120]]
        if not text_lines:
            text_lines = ["ESG Report"]

        content_commands = ["BT", "/F1 10 Tf", "50 790 Td"]
        first_line = True
        for line in text_lines:
            if first_line:
                content_commands.append(f"({line}) Tj")
                first_line = False
            else:
                content_commands.append("0 -14 Td")
                content_commands.append(f"({line}) Tj")
        content_commands.append("ET")
        stream = "\n".join(content_commands).encode("latin-1", errors="replace")

        objects: list[bytes] = [
            b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n",
            b"2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n",
            b"3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>\nendobj\n",
            b"4 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\nendobj\n",
            b"5 0 obj\n<< /Length "
            + str(len(stream)).encode("ascii")
            + b" >>\nstream\n"
            + stream
            + b"\nendstream\nendobj\n",
        ]

        pdf = bytearray(b"%PDF-1.4\n")
        offsets: list[int] = [0]

        for obj in objects:
            offsets.append(len(pdf))
            pdf.extend(obj)

        xref_start = len(pdf)
        pdf.extend(f"xref\n0 {len(objects) + 1}\n".encode("ascii"))
        pdf.extend(b"0000000000 65535 f \n")
        for offset in offsets[1:]:
            pdf.extend(f"{offset:010d} 00000 n \n".encode("ascii"))

        pdf.extend(
            (
                f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\n"
                f"startxref\n{xref_start}\n%%EOF"
            ).encode("ascii")
        )

        return bytes(pdf)

    @staticmethod
    def _to_int(value: Any) -> int | None:
        parsed = ESGWorkflowService._to_float(value)
        if parsed is None:
            return None
        return int(round(parsed))

    @staticmethod
    def _to_float(value: Any) -> float | None:
        try:
            if value is None or value == "":
                return None
            return float(value)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _utc_now_iso() -> str:
        return datetime.now(timezone.utc).isoformat()
