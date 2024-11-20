import base64
import io
from src.kaspi_parser import config
import os
import re
from contextlib import contextmanager
from datetime import datetime

import fitz
import pandas as pd

from src.kaspi_parser import models


def encode_file(file_path: str) -> str:
    """
    Encodes a file to a Base64 string.

    Args:
        file_path (str): The path to the file to be encoded.

    Returns:
        str: The Base64 encoded string representation of the file content.
    """
    with open(file_path, "rb") as file:
        return base64.b64encode(file.read()).decode("utf-8")


class BankStatement:
    """
    A class to process financial statements and extract relevant information.
    """

    def __init__(self) -> None:
        pass

    class Patterns:
        """
        A nested class to store regex patterns for extracting data from financial statements.
        """

        fio_pattern = (
            r"по \d{2}\.\d{2}\.\d{2} (.*?) Номер счета:|бойынша (.*?) Шот нөмірі:"
        )
        card_number_pattern = r"Номер карты: (\*\d{4})|Карта нөмірі: (\*\d{4})"
        iban_pattern = r"Номер счета: (.*?) |Шот нөмірі: (.*?) "
        currency_pattern = r"Валюта счета: (\w+)|Шот валютасы: (\w+)"
        date_pattern = (
            r"за период с (\d{2}\.\d{2}\.\d{2}) по (\d{2}\.\d{2}\.\d{2})"
            r"|(\d{2}\.\d{2}\.\d{2})ж\.? бастап (\d{2}\.\d{2}\.\d{2})ж\.? дейінгі кезеңге"
        )

    def parse_statement(self, file_bytes, date_format="%d.%m.%y"):
        """
        Parse a financial statement from a byte stream.

        Args:
            file_bytes (bytes): The byte content of the financial statement file.
            date_format (str): The date format used in the statement.

        Returns:
            dict: A dictionary containing parsed information from the statement.
        """
        with io.BytesIO(file_bytes) as stream:
            text = self.get_text(stream=stream)
            fio = next(
                (
                    match[0] or match[1]
                    for match in re.findall(
                        self.Patterns.fio_pattern, text, re.IGNORECASE
                    )
                    if any(match)
                ),
                None,
            )
            parts = fio.split()
            filtered_parts = [
                part for i, part in enumerate(parts) if i not in [1, 2, 3]
            ]
            fio = " ".join(filtered_parts)

            card_number = next(
                (
                    match[0] or match[1]
                    for match in re.findall(
                        self.Patterns.card_number_pattern, text, re.IGNORECASE
                    )
                    if any(match)
                ),
                None,
            )

            iban = next(
                (
                    match[0] or match[1]
                    for match in re.findall(
                        self.Patterns.iban_pattern, text, re.IGNORECASE
                    )
                    if any(match)
                ),
                None,
            )

            currency = next(
                (
                    match[0] or match[1]
                    for match in re.findall(
                        self.Patterns.currency_pattern, text, re.IGNORECASE
                    )
                    if any(match)
                ),
                None,
            )

            date_match = next(
                (
                    match
                    for match in re.findall(
                        self.Patterns.date_pattern, text, re.IGNORECASE
                    )
                    if any(match)
                ),
                (None, None, None, None),
            )

            date_from, date_until = (
                date_match[0] or date_match[2],
                date_match[1] or date_match[3],
            )
            card_balance_date_from = self.get_number(
                next(
                    iter(
                        re.findall(
                            rf"(?:Доступно на {date_from}|{date_from}ж. қолжетімді:) (.*?) ₸",
                            text,
                        )
                    ),
                    None,
                ),
                parameter_type="card_balance_date_from",
            )
            card_balance_date_until = self.get_number(
                next(
                    iter(
                        re.findall(
                            rf"(?:Доступно на {date_until}|{date_until}ж. қолжетімді:) (.*?) ₸",
                            text,
                        )
                    ),
                    None,
                ),
                parameter_type="card_balance_date_until",
            )
            replenishments = self.get_number(
                next(iter(re.findall(r"(?:Пополнения|Толықтыру) (.*?) ₸", text)), None)
            )
            transfers = self.get_number(
                next(iter(re.findall(r"(?:Переводы|Аударым) (.*?) ₸", text)), None)
            )
            purchases = self.get_number(
                next(iter(re.findall(r"(?:Покупки|Зат сатып алу) (.*?) ₸", text)), None)
            )
            withdrawals = self.get_number(
                next(iter(re.findall(r"(?:Снятия|Ақша алу) (.*?) ₸", text)), None)
            )
            others = self.get_number(
                next(iter(re.findall(r"(?:Разное|ртүрлі) (.*?) ₸", text)), None)
            )

            date_from, date_until = (
                datetime.strptime(date_from, date_format),
                datetime.strptime(date_until, date_format),
            )

            details = self.get_details(text=text, date_format=date_format)

            result = {
                "financialInstitutionName": "АО «Kaspi Bank»",
                "FIO": fio,
                "cardNumber": card_number,
                "IBAN": iban,
                "currency": currency,
                "fromDate": date_from.strftime(date_format),
                "toDate": date_until.strftime(date_format),
                "cardBalanceDateFrom": card_balance_date_from,
                "cardBalanceDateUntil": card_balance_date_until,
                "Replenishments": replenishments,
                "Transfers": transfers,
                "Purchases": purchases,
                "Withdrawals": withdrawals,
                "Others": others,
                "Details": details,
            }
        return result

    @staticmethod
    def get_text(stream):
        """
        Extract text from a PDF file stream.

        Args:
            stream (io.BytesIO): The byte stream of the PDF file.

        Returns:
            str: The extracted text from the PDF file.
        """
        with fitz.open(stream=stream, filetype="pdf") as pdf:
            text = "\n".join([page.get_text() for page in pdf])
        return " ".join(text.split())

    @staticmethod
    def get_number(value, parameter_type=None):
        """
        Convert a string value to a floating-point number.

        Args:
            value (str): The string representation of the number.
            parameter_type (str, optional): The type of parameter being converted. Defaults to None.

        Returns:
            float: The converted number.
        """
        if value:
            value_ = value.partition("₸")[0]
            value_ = "".join(value_.replace(",", ".").split())
            if parameter_type in ["card_balance_date_from", "card_balance_date_until"]:
                value_ = -float(value_[1:]) if value_.startswith("-") else float(value_)
            else:
                value_ = (
                    -float(value_[1:]) if value_.startswith("-") else float(value_[1:])
                )
            return value_

    @staticmethod
    def get_date(value, date_format):
        """
        Convert a string date to a datetime object.

        Args:
            value (str): The string representation of the date.
            date_format (str): The format of the date string.

        Returns:
            datetime: The converted datetime object.
        """
        return datetime.strptime(value, date_format)

    @staticmethod
    def replace_statement_extra_text(bank_statement_text: str):
        """
        Remove extra text from the bank statement.

        Args:
            bank_statement_text (str): The raw text of the bank statement.

        Returns:
            str: The cleaned text of the bank statement.
        """
        return (
            bank_statement_text.replace(
                "АО «Kaspi Bank», БИК CASPKZKA, www.kaspi.kz", ""
            )
            .replace("«Kaspi Bank» АҚ, БСК CASPKZKA, www.kaspi.kz", "")
            .replace(
                " - Сумма заблокирована. Банк ожидает подтверждения от платежной системы.",
                "",
            )
            .replace(
                " - Сомаға тосқауыл қойылған. Банк төлем жүйесінің растауын күтуде.", ""
            )
        )

    def get_statements(self, bank_statement_text: str) -> list:
        """
        Extract individual statements from the bank statement text.

        Args:
            bank_statement_text (str): The raw text of the bank statement.

        Returns:
            list: A list of tuples containing the date, amount, transaction type, and description.
        """
        bank_statement_text = self.replace_statement_extra_text(bank_statement_text)
        pattern = (
            r"(\d{2}\.\d{2}\.\d{2})\s+"  # Дата в формате dd.mm.yy
            r"([+-]\s?\d{1,3}(?:\s\d{3})*,\d{2} ₸)\s+"  # Сумма с символом валюты
            r"(Перевод|Покупка|Пополнение|Разное|Снятие|"
            r"Толықтыру|Аударым|Зат сатып алу|Ақша алу|Əртүрлі)\s+"  # Тип операции (одно слово)
            r"(.+?)(?=\d{2}\.\d{2}\.\d{2}|$)"  # Описание
        )
        matches = re.findall(pattern, bank_statement_text)
        return [[element.strip() for element in match] for match in matches]

    def get_details(self, text: str, date_format: str = "%d.%m.%y") -> list[dict]:
        """
        Extracts and parses the transaction details from the provided bank statement text.

        Args:
            text (str): The raw text of the bank statement.
            date_format (str, optional): The format of the dates in the statement. Defaults to "%d.%m.%y".

        Returns:
            list[dict]: A list of dictionaries where each dictionary represents a transaction.
                        Each dictionary contains the following keys:
                        - "operationDate" (datetime): The date of the transaction.
                        - "amount" (float): The amount of the transaction.
                        - "transactionType" (str): The type of transaction (e.g., "Transfer", "Purchase").
                        - "detail" (str): Additional details about the transaction.

        """
        statement = self.get_statements(text)
        statement = [
            (
                self.get_date(date, date_format),
                self.get_number(amount),
                operation,
                detail,
            )
            for date, amount, operation, detail in statement
        ]
        details = [
            {
                "operationDate": s[0],
                "amount": s[1],
                "transactionType": s[2],
                "detail": s[3],
            }
            for s in statement
        ]
        return details


class FileProcessor:
    """
    A class responsible for processing data and converting it into an Excel format.
    """

    def __init__(self) -> None:
        """
        Initializes a new instance of the FileProcessor class.
        This class currently does not maintain state and serves as a utility for processing data into Excel format.
        """
        pass

    @staticmethod
    def to_excel(statement_data: dict, file_path: str) -> None:
        """
        Converts the provided statement data into an Excel file and saves it to the specified file path.

        Args:
            statement_data (dict): A dictionary containing parsed statement data, including transaction details and metadata.
            file_path (str): The path where the generated Excel file will be saved.

        Raises:
            FileNotFoundError: If the directory specified in file_path does not exist and cannot be created.
            PermissionError: If the program lacks permission to create the file or directory.

        This function assumes that 'statement_data' includes the keys 'fromDate', 'toDate', 'FIO', 'financialInstitutionName',
        'cardNumber', and 'Details'. Each entry in 'Details' should include 'amount', 'detail', 'operationDate', and 'transactionType'.
        """
        columns = [
            "FROM_DATE",
            "TO_DATE",
            "STATEMENT_LANGUAGE",
            "FULL_NAME",
            "FINANSIAL_INSTITUTION",
            "AMOUNT",
            "DETAILS",
            "OPERATION_DATE",
            "TRANSACTION_TYPE",
            "INSERT_DATE",
            "CARD_NUMBER",
            "ST_CREATION_DATE",
            "ST_MODIFIED_DATE",
            "ST_SUBJECT",
            "ST_AUTHOR",
            "ST_TITLE",
            "ST_PRODUCER",
        ]

        data = []
        for detail in statement_data["Details"]:
            row = [
                statement_data["fromDate"],
                statement_data["toDate"],
                "RUS",
                statement_data["FIO"],
                statement_data["financialInstitutionName"],
                detail["amount"],
                detail["detail"],
                detail["operationDate"],
                detail["transactionType"],
                None,
                statement_data["cardNumber"],
                None,
                None,
                None,
                None,
                None,
                None,
            ]
            data.append(row)
        df = pd.DataFrame(data, columns=columns)
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        df.to_excel(file_path, index=False)


class Record:
    def __init__(self):
        pass

    @staticmethod
    @contextmanager
    def get_db():
        db = models.SessionLocal()
        try:
            yield db
        finally:
            db.close()

    def insert_record(self, statement_data: dict) -> None:
        try:
            bank_statement = models.BankStatement(
                financial_institution_name=statement_data["financialInstitutionName"],
                full_name=statement_data["FIO"],
                card_number=statement_data["cardNumber"],
                iban=statement_data["IBAN"],
                currency=statement_data["currency"],
                from_date=datetime.strptime(statement_data["fromDate"], "%d.%m.%y"),
                to_date=datetime.strptime(statement_data["toDate"], "%d.%m.%y"),
                card_balance_date_from=statement_data["cardBalanceDateFrom"],
                card_balance_date_until=statement_data["cardBalanceDateUntil"],
                replenishments=statement_data["Replenishments"],
                transfers=statement_data["Transfers"],
                purchases=statement_data["Purchases"],
                withdrawals=statement_data["Withdrawals"],
                others=statement_data["Others"]
            )
            with self.get_db() as db:
                config.logging.info("Adding bank_statement to DB")
                db.add(bank_statement)
                db.commit()
                db.refresh(bank_statement)
                config.logging.info(f"BankStatement added with id: {bank_statement.id}")

                for detail in statement_data["Details"]:
                    transaction_detail = models.TransactionDetail(
                        operation_date=detail["operationDate"],
                        amount=detail["amount"],
                        transaction_type=detail["transactionType"],
                        detail=detail["detail"],
                        bank_statement_id=bank_statement.id
                    )

                    db.add(transaction_detail)
                db.commit()
                config.logging.info(f"TransactionDetails added for bank_statement_id: {bank_statement.id}")
        except Exception as error:
            config.logging.error(f'An error occurred while inserting record: {error}')
