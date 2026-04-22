import os
import json
from pathlib import Path
from fastapi import Depends, FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse, Response
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from google import genai  # The new 2026 SDK

from dotenv import load_dotenv

from src.dependencies.engines import GRIEngine
from src.dependencies.services import Services
from src.dependencies.workflow_service import ESGWorkflowService
from src.schemas.input_schemas import ExtractionPromptSchema
from src.schemas.workflow_schemas import (
    ESGReportResponse,
    ESGPlanRequest,
    ESGPlanResponse,
    EvidenceListResponse,
    FileExtractionResponse,
    MonthlyUpdateQuestionsResponse,
    MonthlyUpdateResponse,
    MonthlyUpdateSubmission,
    OnboardingQuizContext,
    OnboardingQuizResponse,
    OnboardingQuizSubmission,
    OnboardingRecommendationResponse,
    ProgressTrackerResponse,
    QuickWinsResponse,
    ResponseLibraryResponse,
)

from src.gris.gri_302_computations import GRI_302_FUNCTIONS
from src.schemas.output_schemas import ExtractedData, GRI_302_REQUIREMENTS
from src.gris.gri_305_computations import GRI_305_FUNCTIONS
from src.schemas.output_schemas import GRI_305_REQUIREMENTS
from src.gris.gri_401_computations import GRI_401_FUNCTIONS
from src.schemas.output_schemas import GRI_401_REQUIREMENTS


load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI):
    api_key = os.environ.get("GEMINI_API_KEY")
    app.state.ai = genai.Client(api_key=api_key).aio if api_key else None
    app.state.GRI302Engine = GRIEngine(GRI_302_FUNCTIONS, GRI_302_REQUIREMENTS)
    app.state.GRI305Engine = GRIEngine(GRI_305_FUNCTIONS, GRI_305_REQUIREMENTS)
    app.state.GRI401Engine = GRIEngine(GRI_401_FUNCTIONS, GRI_401_REQUIREMENTS)
    app.state.workflow_storage_path = (
        Path(__file__).resolve().parents[1] / "storage" / "workflow_data.json"
    )
    yield
    ...


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# initial assumption of structure


@app.post("/get_esg_report")
async def get_esg_report(
    inputs: ExtractionPromptSchema, services: Services = Depends(Services)
) -> dict:

    extracted_data: ExtractedData = await services.ai_extract_data(inputs)

    if extracted_data.detected_gri == "GRI_302":
        computations = services.GRI302Engine.run(extracted_data.data)
        return {
            "extracted_data": extracted_data,
            "processed_data": {
                "302_1_result": computations["302_1"],
                "302_2_result": computations["302_2"],
                "302_3_result": computations["302_3"],
                "302_4_result": computations["302_4"],
                "302_5_result": computations["302_5"],
                "summary": computations["summary"],
            },
        }

    if extracted_data.detected_gri == "GRI_305":
        computations = services.GRI305Engine.run(extracted_data.data)
        return {
            "extracted_data": extracted_data,
            "processed_data": {
                "305_1_result": computations["305_1"],
                "305_2_result": computations["305_2"],
                "305_3_result": computations["305_3"],
                "305_4_result": computations["305_4"],
                "305_5_result": computations["305_5"],
                "305_6_result": computations["305_6"],
                "305_7_result": computations["305_7"],
                "summary": computations["summary"],
            },
        }

    if extracted_data.detected_gri == "GRI_401":
        computations = services.GRI401Engine.run(extracted_data.data)
        return {
            "extracted_data": extracted_data,
            "processed_data": {
                "401_1_result": computations["401_1"],
                "401_2_result": computations["401_2"],
                "401_3_result": computations["401_3"],
                "summary": computations["summary"],
            },
        }

    raise HTTPException(
        status_code=422,
        detail="Unsupported or undetected GRI standard in extracted payload.",
    )


@app.get("/test")
async def test(services=Depends(Services)):
    response = await services.ai.models.generate_content(
        model="gemini-2.5-flash", contents="How does AI work?"
    )

    return response.model_dump_json


@app.post("/workflow/onboarding/quiz", response_model=OnboardingQuizResponse)
def get_onboarding_quiz(
    context: OnboardingQuizContext,
    workflow: ESGWorkflowService = Depends(ESGWorkflowService),
) -> OnboardingQuizResponse:
    return workflow.get_onboarding_quiz(context)


@app.post(
    "/workflow/onboarding/submit", response_model=OnboardingRecommendationResponse
)
async def submit_onboarding(
    submission: OnboardingQuizSubmission,
    workflow: ESGWorkflowService = Depends(ESGWorkflowService),
) -> OnboardingRecommendationResponse:
    return await workflow.submit_onboarding(submission)


@app.post("/workflow/plan/generate", response_model=ESGPlanResponse)
async def generate_esg_plan(
    plan_request: ESGPlanRequest,
    workflow: ESGWorkflowService = Depends(ESGWorkflowService),
) -> ESGPlanResponse:
    return await workflow.generate_plan(plan_request)


@app.post("/workflow/files/upload", response_model=FileExtractionResponse)
async def upload_esg_files(
    company_id: str = Form(...),
    notes: str | None = Form(default=None),
    files: list[UploadFile] = File(...),
    workflow: ESGWorkflowService = Depends(ESGWorkflowService),
) -> FileExtractionResponse:
    return await workflow.upload_files(company_id=company_id, files=files, notes=notes)


@app.get(
    "/workflow/response-library/{company_id}", response_model=ResponseLibraryResponse
)
def get_response_library(
    company_id: str,
    limit: int = 50,
    workflow: ESGWorkflowService = Depends(ESGWorkflowService),
) -> ResponseLibraryResponse:
    return workflow.get_response_library(company_id, limit)


@app.post("/workflow/reset/{company_id}")
def reset_workflow_artifacts(
    company_id: str,
    workflow: ESGWorkflowService = Depends(ESGWorkflowService),
) -> dict[str, str]:
    return workflow.reset_reporting_artifacts(company_id)


@app.get("/workflow/progress/{company_id}", response_model=ProgressTrackerResponse)
def get_progress_tracker(
    company_id: str,
    workflow: ESGWorkflowService = Depends(ESGWorkflowService),
) -> ProgressTrackerResponse:
    return workflow.get_progress(company_id)


@app.get("/workflow/quick-wins/{company_id}", response_model=QuickWinsResponse)
def get_quick_wins(
    company_id: str,
    workflow: ESGWorkflowService = Depends(ESGWorkflowService),
) -> QuickWinsResponse:
    return workflow.get_quick_wins(company_id)


@app.get(
    "/workflow/monthly-update/{company_id}/questions",
    response_model=MonthlyUpdateQuestionsResponse,
)
def get_monthly_update_questions(
    company_id: str,
    month: str | None = None,
    workflow: ESGWorkflowService = Depends(ESGWorkflowService),
) -> MonthlyUpdateQuestionsResponse:
    return workflow.get_monthly_update_questions(company_id=company_id, month=month)


@app.post("/workflow/monthly-update/submit", response_model=MonthlyUpdateResponse)
async def submit_monthly_update(
    submission: MonthlyUpdateSubmission,
    workflow: ESGWorkflowService = Depends(ESGWorkflowService),
) -> MonthlyUpdateResponse:
    return await workflow.submit_monthly_update(submission)


@app.post(
    "/workflow/monthly-update/submit-with-files",
    response_model=MonthlyUpdateResponse,
)
async def submit_monthly_update_with_files(
    company_id: str = Form(...),
    month: str = Form(...),
    changes_json: str | None = Form(default=None),
    notes: str | None = Form(default=None),
    files: list[UploadFile] = File(...),
    workflow: ESGWorkflowService = Depends(ESGWorkflowService),
) -> MonthlyUpdateResponse:
    try:
        parsed_changes = json.loads(changes_json) if changes_json else {}
    except json.JSONDecodeError as exc:
        raise HTTPException(
            status_code=422,
            detail="changes_json must be a valid JSON object string.",
        ) from exc

    submission = MonthlyUpdateSubmission(
        company_id=company_id,
        month=month,
        changes=parsed_changes,
        notes=notes,
    )
    return await workflow.submit_monthly_update_with_files(submission, files)


@app.get("/evidence/{company_id}", response_model=EvidenceListResponse)
def list_evidence(
    company_id: str,
    workflow: ESGWorkflowService = Depends(ESGWorkflowService),
) -> EvidenceListResponse:
    return workflow.list_evidence(company_id)


@app.get("/evidence/{company_id}/{file_id}")
def download_evidence(
    company_id: str,
    file_id: str,
    workflow: ESGWorkflowService = Depends(ESGWorkflowService),
) -> FileResponse:
    file_path, metadata = workflow.resolve_evidence_file(company_id, file_id)
    filename = metadata.get("filename") or file_id
    media_type = metadata.get("media_type") or "application/octet-stream"
    return FileResponse(
        path=file_path,
        filename=filename,
        media_type=media_type,
    )


@app.delete("/evidence/{company_id}/{file_id}", status_code=204)
def delete_evidence(
    company_id: str,
    file_id: str,
    workflow: ESGWorkflowService = Depends(ESGWorkflowService),
) -> Response:
    workflow.delete_evidence_file(company_id, file_id)
    return Response(status_code=204)


@app.get("/workflow/report/{company_id}", response_model=ESGReportResponse)
def get_workflow_report(
    company_id: str,
    workflow: ESGWorkflowService = Depends(ESGWorkflowService),
) -> ESGReportResponse:
    return workflow.get_esg_report(company_id)


@app.get("/workflow/report/{company_id}/pdf")
def download_workflow_report_pdf(
    company_id: str,
    workflow: ESGWorkflowService = Depends(ESGWorkflowService),
) -> Response:
    filename, pdf_bytes = workflow.get_esg_report_pdf(company_id)
    headers = {
        "Content-Disposition": f'attachment; filename="{filename}"',
    }
    return Response(content=pdf_bytes, media_type="application/pdf", headers=headers)
