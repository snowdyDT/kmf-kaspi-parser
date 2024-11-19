from pydantic import BaseModel


class PDFRequest(BaseModel):
    base64_pdf: str
