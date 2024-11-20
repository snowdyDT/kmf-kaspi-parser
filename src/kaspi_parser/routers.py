import base64
import uuid

from fastapi import APIRouter, HTTPException

from src.kaspi_parser import config
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
        config.logging.info(
            f"Starting to parse PDF for base64 input: {request.base64_pdf[:50]}..."
        )
        pdf_bytes = base64.b64decode(request.base64_pdf)
        statement_data = bank_statement.parse_statement(file_bytes=pdf_bytes)
        success = True if statement_data else False
        config.logging.info(f"PDF parsing successful: {success}")

        if request.to_excel is True and success is True:
            file_id = str(uuid.uuid4()).replace("-", "_")
            file_path = f"assets/output/statement_{file_id}.xlsx"
            file_processor.to_excel(statement_data=statement_data, file_path=file_path)
            config.logging.info(f"Excel file generated: {file_path}")
        if request.dry_run is False and success is True:
            config.logging.info("Dry run is False, inserting record into database...")
            record.insert_record(statement_data=statement_data)
            config.logging.info("Record inserted into database successfully.")
        return {
            "success": success,
            "msg": None,
            "msgType": None,
            "excel_path": file_path,
            "data": statement_data,
        }
    except Exception as error:
        config.logging.error(f"Error parsing PDF: {error}")
        raise HTTPException(status_code=400, detail=f"Error parsing PDF: {error}")
