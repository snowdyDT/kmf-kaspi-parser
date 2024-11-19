import base64

from fastapi import APIRouter, HTTPException

from src.kaspi_parser import models
from src.kaspi_parser import util

router = APIRouter()
file_processor = util.FileProcessor()


@router.post("/parse-statement/")
async def parse_statement(request: models.PDFRequest):
    try:
        pdf_bytes = base64.b64decode(request.base64_pdf)
        statement_data = file_processor.parse_statement(path=pdf_bytes)
        return {"success": True, "data": statement_data}
    except Exception as error:
        raise HTTPException(status_code=400, detail=f"Error parsing PDF: {error}")
