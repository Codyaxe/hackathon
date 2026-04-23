from fastapi import Request
from google import genai
from google.genai import types # Important for specific Type hints

from src.schemas.input_schemas import ExtractionPromptSchema
from src.schemas.output_schemas import ExtractedData

class Services:
    def __init__(self, request: Request):
        # We access the .aio property from the client stored in state
        self.ai = request.app.state.ai
        self.GRI302Engine = request.app.state.GRI302Engine
        self.GRI305Engine = request.app.state.GRI305Engine
        self.GRI401Engine = request.app.state.GRI401Engine



    async def ai_extract_data(self, inputs: ExtractionPromptSchema) -> dict:
        # Construct the parts list
        # 1. Start with your instructions/text
        prompt_parts = [
            types.Part.from_text(text="""Analyze the following prompt inputs and extract relevant data for
                                    ESG Reporting (using GRI Framework).""")
        ]

        if inputs.free_form != None:
            prompt_parts.append(types.Part.from_text(text=inputs.free_form))

        # 2. Add the Image bytes (assuming inputs.photo is bytes)
        for photo in inputs.photos:
            prompt_parts.append(
                types.Part.from_bytes(
                    data=photo.data,
                    mime_type=photo.media_type
                )
            )

        for pdf in inputs.pdfs:
            prompt_parts.append(
                types.Part.from_bytes(
                    data=pdf.data,
                    mime_type=pdf.media_type
                )
            )

        # Send to Gemini
        response = await self.ai.models.generate_content(
            model="gemini-3-flash-preview", # Flash is great for multi-document parsing
            contents=prompt_parts,
            config=types.GenerateContentConfig(
                #tools=[types.Tool(google_search=types.GoogleSearch())],
                response_mime_type="application/json",
                response_schema=ExtractedData, 
            ),
        )

        return response.parsed