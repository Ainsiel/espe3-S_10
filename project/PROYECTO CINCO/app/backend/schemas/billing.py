"""schemas/billing.py — Schemas de facturación."""
from datetime import datetime
from decimal import Decimal
from typing import Optional, List
from pydantic import BaseModel, field_validator


class InvoiceLineCreate(BaseModel):
    product_id: Optional[int] = None
    description: str
    quantity: Decimal
    unit_price: Decimal
    discount_pct: Decimal = Decimal("0")
    tax_rate: Decimal = Decimal("19")


class InvoiceCreate(BaseModel):
    company_id: int = 1
    customer_id: int
    sales_order_id: Optional[int] = None
    number: str
    issued_at: datetime
    due_date: Optional[datetime] = None
    notes: Optional[str] = None
    lines: List[InvoiceLineCreate]


class InvoiceRead(BaseModel):
    id: int
    customer_id: int
    number: str
    status: str
    issued_at: datetime
    net_amount: Decimal
    tax_amount: Decimal
    total: Decimal
    balance: Decimal
    created_at: datetime
    model_config = {"from_attributes": True}


class PaymentCreate(BaseModel):
    invoice_id: int
    amount: Decimal
    method: str
    reference: Optional[str] = None
    payment_date: datetime

    @field_validator("amount")
    @classmethod
    def positive(cls, v):
        if v <= 0:
            raise ValueError("Monto debe ser > 0")
        return v


class PaymentRead(BaseModel):
    id: int
    invoice_id: int
    amount: Decimal
    method: str
    payment_date: datetime
    status: str
    model_config = {"from_attributes": True}


class CreditNoteCreate(BaseModel):
    invoice_id: int
    sales_return_id: Optional[int] = None
    number: str
    reason: str
    total: Decimal


class DebitNoteCreate(BaseModel):
    invoice_id: int
    number: str
    concept: str
    total: Decimal
    tax_amount: Decimal = Decimal("0")
