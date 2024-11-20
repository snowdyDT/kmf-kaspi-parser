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
        statement_data = file_processor.parse_statement(file_bytes=pdf_bytes)
        success = True if statement_data else False
        return {
            "success": success,
            "msg": None,
            "msgType": None,
            "data": statement_data,
        }
    except Exception as error:
        raise HTTPException(status_code=400, detail=f"Error parsing PDF: {error}")
