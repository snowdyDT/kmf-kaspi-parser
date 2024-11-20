from fastapi.testclient import TestClient
from src.kaspi_parser.main import app

client = TestClient(app)


def test_parse_statement(sample_pdf_base64):
    assert isinstance(sample_pdf_base64, str)
    response = client.post("/parse-statement/", json={"base64_pdf": sample_pdf_base64})
    assert response.status_code == 200
    json_response = response.json()
    assert json_response["success"] is True
    assert "data" in json_response


def test_parse_statement_to_excel(sample_pdf_base64):
    assert isinstance(sample_pdf_base64, str)
    response = client.post("/parse-statement/", json={"base64_pdf": sample_pdf_base64, 'to_excel': True})
    assert response.status_code == 200
    json_response = response.json()
    assert json_response["success"] is True
    assert "data" in json_response
