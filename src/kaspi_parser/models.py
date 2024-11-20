from pydantic import BaseModel
from sqlalchemy import Column, String, Float, Date, DateTime, Integer, ForeignKey
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker

from src.kaspi_parser import config

Base = declarative_base()


class PDFRequest(BaseModel):
    base64_pdf: str
    to_excel: bool = False
    dry_run: bool = False


class BankStatement(Base):
    __tablename__ = 'bank_statements'

    id = Column(Integer, primary_key=True, index=True)
    financial_institution_name = Column(String(256), nullable=False)
    full_name = Column(String(256), nullable=False)
    card_number = Column(String(20), nullable=False)
    iban = Column(String(34), nullable=False)
    currency = Column(String(10), nullable=False)
    from_date = Column(Date, nullable=False)
    to_date = Column(Date, nullable=False)
    card_balance_date_from = Column(Float, nullable=False)
    card_balance_date_until = Column(Float, nullable=False)
    replenishments = Column(Float, nullable=False)
    transfers = Column(Float, nullable=False)
    purchases = Column(Float, nullable=False)
    withdrawals = Column(Float, nullable=False)
    others = Column(Float, nullable=False)

    details = relationship("TransactionDetail", back_populates="bank_statement")


class TransactionDetail(Base):
    __tablename__ = 'transaction_details'

    id = Column(Integer, primary_key=True, index=True)
    operation_date = Column(DateTime, nullable=False)
    amount = Column(Float, nullable=False)
    transaction_type = Column(String(50), nullable=False)
    detail = Column(String(256), nullable=True)
    bank_statement_id = Column(Integer, ForeignKey('bank_statements.id'))

    bank_statement = relationship("BankStatement", back_populates="details")


engine = create_engine(config.DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)
