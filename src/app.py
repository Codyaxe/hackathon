import os
from fastapi import Depends, FastAPI, HTTPException
from contextlib import asynccontextmanager
from google import genai # The new 2026 SDK

from dotenv import load_dotenv

from src.dependencies.engines import GRIEngine
from src.dependencies.services import Services
from src.schemas.input_schemas import ExtractionPromptSchema

from src.gris.gri_302_computations import GRI_302_FUNCTIONS
from src.schemas.output_schemas import GRI_302_REQUIREMENTS
from src.gris.gri_305_computations import GRI_305_FUNCTIONS
from src.schemas.output_schemas import GRI_305_REQUIREMENTS




load_dotenv()

@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.ai = genai.Client(api_key=os.environ.get("GEMINI_API_KEY")).aio
    app.state.GRI302Engine = GRIEngine(GRI_302_FUNCTIONS, GRI_302_REQUIREMENTS)
    app.state.GRI305Engine = GRIEngine(GRI_305_FUNCTIONS, GRI_305_REQUIREMENTS)
    yield
    ...



app = FastAPI(lifespan=lifespan)


# initial assumption of structure

@app.post("/get_esg_report")
async def get_esg_report(inputs: ExtractionPromptSchema, services: Services = Depends(Services)) -> dict:
    
    extracted_data = await services.ai_extract_data(inputs)

    if extracted_data.detected_gri == "GRI_302":
        computations = services.GRI302Engine.run(extracted_data.data)
        return {
                "extracted_data":extracted_data,
                "processed_data":{
                "302_1_result": computations["302_1"],
                "302_2_result": computations["302_2"],
                "302_3_result": computations["302_3"],
                "302_4_result": computations["302_4"],
                "302_5_result": computations["302_5"],
                "summary": computations["summary"],
                }
        }

    if extracted_data.detected_gri == "GRI_305":
        computations = services.GRI305Engine.run(extracted_data.data)
        return {
            "extracted_data":extracted_data,
            "processed_data":{
                "305_1_result": computations["305_1"],
                "305_2_result": computations["305_2"],
                "305_3_result": computations["305_3"],
                "305_4_result": computations["305_4"],
                "305_5_result": computations["305_5"],
                "305_6_result": computations["305_6"],
                "305_7_result": computations["305_7"],
                "summary": computations["summary"],
                }
        }

    if extracted_data.detected_gri == "GRI_401":
        raise HTTPException(
            status_code=501,
            detail="GRI standard not yet implemented",
        )







@app.get("/test")
async def test(services = Depends(Services)):
    response = services.ai.models.generate_content(
        model="gemini-2.5-flash",
        contents="How does AI work?"
    )

    return response.model_dump_json