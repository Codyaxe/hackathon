from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import re
from typing import Any, Literal, cast
from uuid import uuid4

from fastapi import HTTPException, Request, UploadFile
from google.genai import types

from src.dependencies.repository import ESGRepository
from src.schemas.workflow_schemas import (
    AIFileExtractionResult,
    ESGPlanAction,
    ESGPlanRequest,
    ESGPlanResponse,
    ExtractedMetric,
    FileExtractionResponse,
    FocusArea,
    MonthlyUpdateQuestion,
    MonthlyUpdateQuestionsResponse,
    MonthlyUpdateResponse,
    MonthlyUpdateSubmission,
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


class ESGWorkflowService:
    """Application service for onboarding, planning, uploads, and progress workflows."""

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
        self.ai = request.app.state.ai
        self.repo = ESGRepository(Path(request.app.state.workflow_storage_path))

    def get_onboarding_quiz(self, context) -> OnboardingQuizResponse:
        questions = self._build_onboarding_questions(
            context.industry, context.employee_count
        )
        self.repo.save_profile(context.company_id, context.model_dump(mode="json"))
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

        plan_response = ESGPlanResponse(
            company_id=plan_request.company_id,
            generated_at=datetime.now(timezone.utc),
            one_page_summary=one_page_summary,
            priority_themes=selected_themes,
            actions=actions,
            monthly_check_in_questions=monthly_questions,
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

        upload_records: list[UploadedFileRecord] = []

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
            )
            upload_records.append(record)

            if media_type in {"text/csv", "text/plain"}:
                text_preview = binary.decode("utf-8", errors="ignore")[:20000]
                file_parts.append(
                    types.Part.from_text(
                        text=f"File: {record.filename}\nContent preview:\n{text_preview}"
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

        extraction = await self._extract_metrics_with_ai(file_parts, upload_records)
        response = FileExtractionResponse(
            company_id=company_id,
            files=upload_records,
            extracted_metrics=extraction.metrics,
            ai_summary=extraction.summary,
            follow_up_questions=extraction.follow_up_questions,
        )

        response_payload = response.model_dump(mode="json")
        self.repo.save_upload_batch(
            company_id,
            upload_records=[
                record.model_dump(mode="json") for record in upload_records
            ],
            extraction_payload=response_payload,
        )
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

        return ProgressTrackerResponse(
            company_id=company_id,
            completion_percentage=completion,
            maturity_stage=maturity,
            steps=steps,
            next_best_actions=next_actions,
        )

    def get_quick_wins(self, company_id: str) -> QuickWinsResponse:
        company_data = self.repo.get_company_data(company_id)
        if not company_data:
            raise HTTPException(
                status_code=404, detail="Company not found. Complete onboarding first."
            )

        onboarding = company_data.get("onboarding", {})
        focus_areas = [
            item.get("area", "") for item in onboarding.get("focus_areas", [])
        ]
        if not focus_areas:
            focus_areas = self._default_focus_by_industry(
                company_data.get("profile", {}).get("industry", "")
            )

        suggestions_by_area = {
            "energy": QuickWinItem(
                title="Track energy from last 3 utility bills",
                impact_area="energy",
                effort="low",
                expected_benefit="Find immediate savings opportunities and establish baseline usage.",
                why_recommended="Energy tracking is usually the fastest way for SMEs to see measurable ESG progress.",
                first_step="Create one monthly sheet with kWh and cost by facility.",
            ),
            "emissions": QuickWinItem(
                title="Estimate Scope 1 + 2 using existing bills",
                impact_area="emissions",
                effort="low",
                expected_benefit="Create your first carbon snapshot without complex tooling.",
                why_recommended="You already have enough data from fuel and electricity documents.",
                first_step="Map electricity and fuel totals to a simple emissions calculator.",
            ),
            "waste": QuickWinItem(
                title="Run a one-week waste separation trial",
                impact_area="waste",
                effort="low",
                expected_benefit="Cut landfill waste quickly and improve recycling rates.",
                why_recommended="Small process changes often deliver visible waste improvements in under a month.",
                first_step="Label waste streams and record weekly weights by category.",
            ),
            "workforce": QuickWinItem(
                title="Start a monthly workforce wellbeing pulse",
                impact_area="workforce",
                effort="low",
                expected_benefit="Spot retention and safety risks early with lightweight tracking.",
                why_recommended="People metrics are often under-tracked but highly impactful for ESG maturity.",
                first_step="Use a 5-question anonymous survey and monitor trend lines.",
            ),
            "governance": QuickWinItem(
                title="Assign ESG ownership and a 30-minute monthly review",
                impact_area="governance",
                effort="low",
                expected_benefit="Turns ESG from ad-hoc efforts into repeatable execution.",
                why_recommended="Clear ownership is the single biggest predictor of sustained progress.",
                first_step="Nominate one owner and create a recurring review meeting.",
            ),
            "data_foundation": QuickWinItem(
                title="Build one shared ESG data template",
                impact_area="data_foundation",
                effort="low",
                expected_benefit="Avoid rework and make monthly updates take minutes, not hours.",
                why_recommended="A clean data template removes the biggest SME ESG bottleneck.",
                first_step="Define core fields for energy, emissions, waste, and headcount.",
            ),
            "supply_chain": QuickWinItem(
                title="Collect top-5 supplier sustainability details",
                impact_area="supply_chain",
                effort="medium",
                expected_benefit="Improve procurement risk visibility and customer trust.",
                why_recommended="Most SMEs can start supply chain ESG with a small supplier subset.",
                first_step="Request environmental and labor policy docs from your largest suppliers.",
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

        return QuickWinsResponse(
            company_id=company_id,
            generated_at=datetime.now(timezone.utc),
            quick_wins=quick_wins,
        )

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

    def submit_monthly_update(
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

        self.repo.save_monthly_update(submission.company_id, payload)
        self.repo.append_library_entry(submission.company_id, "monthly_update", payload)

        return MonthlyUpdateResponse(
            company_id=submission.company_id,
            month=submission.month,
            change_summary=summary,
            updated_focus_areas=updated_focus,
            recommended_next_actions=recommended_next_actions,
        )

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
    ) -> AIFileExtractionResult:
        if self.ai is None:
            return self._fallback_file_extraction(upload_records)

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

        return self._fallback_file_extraction(upload_records)

    def _fallback_file_extraction(
        self, upload_records: list[UploadedFileRecord]
    ) -> AIFileExtractionResult:
        metrics: list[ExtractedMetric] = []

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
            summary="Files were uploaded successfully. Please review suggested fields and refine where needed.",
            metrics=metrics,
            follow_up_questions=[
                "Which month or reporting period do these files represent?",
                "Do you want extraction to prioritize energy, emissions, workforce, or waste metrics?",
            ],
        )

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
