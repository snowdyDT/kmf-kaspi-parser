import base64

from fastapi import APIRouter, HTTPException
import uuid
from src.kaspi_parser import models
from src.kaspi_parser import util

router = APIRouter()
bank_statement = util.BankStatement()
file_processor = util.FileProcessor()
record = util.Record()


@router.post("/parse-statement/")
async def parse_statement(request: models.PDFRequest):
    file_path = ""
    try:
        pdf_bytes = base64.b64decode(request.base64_pdf)
        statement_data = bank_statement.parse_statement(file_bytes=pdf_bytes)
        success = True if statement_data else False
        if request.to_excel is True and success is True:
            file_id = str(uuid.uuid4()).replace("-", "_")
            file_path = f"assets/output/statement_{file_id}.xlsx"
            file_processor.to_excel(statement_data=statement_data, file_path=file_path)
        if request.dry_run is False and success is True:
            record.insert_record(statement_data=statement_data)
        return {
            "success": success,
            "msg": None,
            "msgType": None,
            "excel_path": file_path,
            "data": statement_data,
        }
    except Exception as error:
        raise HTTPException(status_code=400, detail=f"Error parsing PDF: {error}")
