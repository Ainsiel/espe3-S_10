"""schemas/sales.py — Schemas de ventas, cotizaciones, despachos y devoluciones."""
from datetime import datetime
from decimal import Decimal
from typing import Optional, List
from pydantic import BaseModel, field_validator


class SalesOrderLineCreate(BaseModel):
    product_id: int
    quantity: Decimal
    unit_price: Decimal
    discount_pct: Decimal = Decimal("0")
    tax_rate: Decimal = Decimal("19")

    @field_validator("quantity", "unit_price")
    @classmethod
    def positive(cls, v):
        if v <= 0:
            raise ValueError("Debe ser > 0")
        return v


class SalesOrderLineRead(BaseModel):
    id: int
    product_id: int
    quantity: Decimal
    dispatched_qty: Decimal
    unit_price: Decimal
    discount_pct: Decimal
    tax_rate: Decimal
    subtotal: Decimal
    model_config = {"from_attributes": True}


class SalesOrderCreate(BaseModel):
    company_id: int = 1
    customer_id: int
    quotation_id: Optional[int] = None
    delivery_date: Optional[datetime] = None
    payment_term_days: int = 0
    notes: Optional[str] = None
    lines: List[SalesOrderLineCreate]

    @field_validator("lines")
    @classmethod
    def at_least_one_line(cls, v):
        if not v:
            raise ValueError("Orden requiere al menos una línea")
        return v


class SalesOrderUpdate(BaseModel):
    delivery_date: Optional[datetime] = None
    notes: Optional[str] = None


class SalesOrderRead(BaseModel):
    id: int
    company_id: int
    customer_id: int
    number: Optional[str]
    status: str
    order_date: datetime
    subtotal: Decimal
    tax_total: Decimal
    total: Decimal
    lines: List[SalesOrderLineRead] = []
    model_config = {"from_attributes": True}


class QuotationLineCreate(BaseModel):
    product_id: int
    quantity: Decimal
    unit_price: Decimal
    discount_pct: Decimal = Decimal("0")
    tax_rate: Decimal = Decimal("19")


class QuotationCreate(BaseModel):
    company_id: int = 1
    customer_id: int
    expires_at: Optional[datetime] = None
    notes: Optional[str] = None
    lines: List[QuotationLineCreate]


class QuotationRead(BaseModel):
    id: int
    customer_id: int
    number: Optional[str]
    status: str
    expires_at: Optional[datetime]
    total: Decimal
    model_config = {"from_attributes": True}


class DispatchLineCreate(BaseModel):
    sales_order_line_id: int
    product_id: int
    quantity: Decimal


class DispatchCreate(BaseModel):
    sales_order_id: int
    warehouse_id: int
    notes: Optional[str] = None
    lines: List[DispatchLineCreate]


class ReturnLineCreate(BaseModel):
    sales_order_line_id: int
    product_id: int
    quantity: Decimal
    unit_price: Decimal = Decimal("0")


class ReturnCreate(BaseModel):
    company_id: int = 1
    sales_order_id: int
    customer_id: int
    reason: str
    lines: List[ReturnLineCreate]

    @field_validator("reason")
    @classmethod
    def reason_required(cls, v):
        if not v or not v.strip():
            raise ValueError("Motivo obligatorio en devolución")
        return v


class ReturnRead(BaseModel):
    id: int
    sales_order_id: int
    customer_id: int
    reason: str
    status: str
    total: Decimal
    created_at: datetime
    model_config = {"from_attributes": True}
