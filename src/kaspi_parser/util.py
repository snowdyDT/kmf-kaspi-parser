import base64
import io
import re
from datetime import datetime

import fitz


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


class FileProcessor:
    class Patterns:
        fio_pattern = r'по \d{2}\.\d{2}\.\d{2} (.*?) Номер счета:|бойынша (.*?) Шот нөмірі:'
        card_number_pattern = r'Номер карты: (\*\d{4})|Карта нөмірі: (\*\d{4})'
        iban_pattern = r'Номер счета: (.*?) |Шот нөмірі: (.*?) '
        currency_pattern = r'Валюта счета: (\w+)|Шот валютасы: (\w+)'
        date_pattern = (r'за период с (\d{2}\.\d{2}\.\d{2}) по (\d{2}\.\d{2}\.\d{2})'
                        r'|(\d{2}\.\d{2}\.\d{2})ж\.? бастап (\d{2}\.\d{2}\.\d{2})ж\.? дейінгі кезеңге')

    def parse_statement(self, file_bytes):
        result = None
        date_format = '%d.%m.%y'

        with io.BytesIO(file_bytes) as file:
            text = self.get_text(file=file)
            fio = next(
                (match[0] or match[1] for match in re.findall(self.Patterns.fio_pattern, text, re.IGNORECASE) if
                 any(match)),
                None)
            parts = fio.split()
            filtered_parts = [part for i, part in enumerate(parts) if i not in [1, 2, 3]]
            fio = ' '.join(filtered_parts)

            card_number = next(
                (match[0] or match[1] for match in re.findall(self.Patterns.card_number_pattern, text, re.IGNORECASE) if
                 any(match)), None)

            iban = next(
                (match[0] or match[1] for match in re.findall(self.Patterns.iban_pattern, text, re.IGNORECASE) if
                 any(match)),
                None)

            currency = next(
                (match[0] or match[1] for match in re.findall(self.Patterns.currency_pattern, text, re.IGNORECASE) if
                 any(match)), None)

            date_match = next(
                (match for match in re.findall(self.Patterns.date_pattern, text, re.IGNORECASE) if any(match)),
                (None, None, None, None))

            date_from, date_until = date_match[0] or date_match[2], date_match[1] or date_match[3]
            card_balance_date_from = self.get_number(
                next(iter(
                    re.findall(rf'(?:Доступно на {date_from}|{date_from}ж. қолжетімді:) (.*?) ₸', text)),
                    None),
                parameter_type='card_balance_date_from'
            )
            card_balance_date_until = self.get_number(
                next(iter(
                    re.findall(rf'(?:Доступно на {date_until}|{date_until}ж. қолжетімді:) (.*?) ₸', text)),
                    None),
                parameter_type='card_balance_date_until'
            )
            replenishments = self.get_number(
                next(iter(re.findall(r'(?:Пополнения|Толықтыру) (.*?) ₸', text)), None))
            transfers = self.get_number(
                next(iter(re.findall(r'(?:Переводы|Аударым) (.*?) ₸', text)), None))
            purchases = self.get_number(
                next(iter(re.findall(r'(?:Покупки|Зат сатып алу) (.*?) ₸', text)), None))
            withdrawals = self.get_number(
                next(iter(re.findall(r'(?:Снятия|Ақша алу) (.*?) ₸', text)), None))
            others = self.get_number(
                next(iter(re.findall(r'(?:Разное|ртүрлі) (.*?) ₸', text)), None))

            statement = self.get_statements(text)
            statement = [
                (self.get_date(date, date_format), self.get_number(amount), operation, detail)
                for date, amount, operation, detail in statement
            ]

            date_from, date_until = \
                datetime.strptime(date_from, date_format), datetime.strptime(date_until,
                                                                             date_format)

            result = {
                'Bank': 'АО «Kaspi Bank»',
                'FIO': fio,
                'cardNumber': card_number,
                'IBAN': iban,
                'currency': currency,
                'dateFrom': date_from.strftime(date_format),
                'dateUntil': date_until.strftime(date_format),
                'cardBalanceDateFrom': card_balance_date_from,
                'cardBalanceDateUntil': card_balance_date_until,
                'Replenishments': replenishments,
                'Transfers': transfers,
                'Purchases': purchases,
                'Withdrawals': withdrawals,
                'Others': others,
            }
        return result

    @staticmethod
    def get_text(file: bytes):
        with fitz.open(file) as file:
            text = ""
            for page_num in range(len(file)):
                page = file.load_page(page_num)  # загружаем страницу
                text += page.extract_text()
        return text

    @staticmethod
    def get_number(value, parameter_type=None):
        if value:
            value_ = value.partition('₸')[0]
            value_ = ''.join(value_.replace(',', '.').split())
            if parameter_type in ['card_balance_date_from', 'card_balance_date_until']:
                value_ = -float(value_[1:]) if value_.startswith('-') else float(value_)
            else:
                value_ = -float(value_[1:]) if value_.startswith('-') else float(value_[1:])
            return value_

    @staticmethod
    def get_date(value, date_format):
        return datetime.strptime(value, date_format)

    @staticmethod
    def replace_statement_extra_text(bank_statement_text: str):
        return bank_statement_text.replace('АО «Kaspi Bank», БИК CASPKZKA, www.kaspi.kz', '') \
            .replace('«Kaspi Bank» АҚ, БСК CASPKZKA, www.kaspi.kz', '') \
            .replace(' - Сумма заблокирована. Банк ожидает подтверждения от платежной системы.', '') \
            .replace(' - Сомаға тосқауыл қойылған. Банк төлем жүйесінің растауын күтуде.', '')

    def get_statements(self, bank_statement_text: str) -> list:
        bank_statement_text = self.replace_statement_extra_text(bank_statement_text)
        pattern = (
            r'(\d{2}\.\d{2}\.\d{2})\s+'  # Дата в формате dd.mm.yy
            r'([+-]\s?\d{1,3}(?:\s\d{3})*,\d{2} ₸)\s+'  # Сумма с символом валюты
            r'(Перевод|Покупка|Пополнение|Разное|Снятие|'
            r'Толықтыру|Аударым|Зат сатып алу|Ақша алу|Əртүрлі)\s+'  # Тип операции (одно слово)
            r'(.+?)(?=\d{2}\.\d{2}\.\d{2}|$)'  # Описание
        )
        matches = re.findall(pattern, bank_statement_text)
        return [[element.strip() for element in match] for match in matches]
