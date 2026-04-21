from pydantic import BaseModel, Field



class FileData(BaseModel):
    data: bytes
    media_type: str  # e.g., "image/jpeg" or "application/pdf"

class ExtractionPromptSchema(BaseModel):
    free_form: str
    photos: list[FileData] = []
    pdfs: list[FileData] = []