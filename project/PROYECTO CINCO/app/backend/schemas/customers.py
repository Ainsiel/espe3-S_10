"""schemas/customers.py — Schemas de clientes y contactos."""
from datetime import datetime
from decimal import Decimal
from typing import Optional, List
from pydantic import BaseModel, field_validator
import re


class ContactCreate(BaseModel):
    name: str
    position: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    is_primary: bool = False


class ContactRead(BaseModel):
    id: int
    customer_id: int
    name: str
    position: Optional[str]
    email: Optional[str]
    phone: Optional[str]
    is_primary: bool
    model_config = {"from_attributes": True}


class CustomerCreate(BaseModel):
    company_id: int = 1
    legal_name: str
    trade_name: Optional[str] = None
    tax_id: str
    business_activity: Optional[str] = None
    billing_email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    country: str = "Chile"
    payment_term_days: int = 0
    credit_limit: Decimal = Decimal("0")
    notes: Optional[str] = None

    @field_validator("tax_id")
    @classmethod
    def strip_tax_id(cls, v):
        v = v.strip()
        if not v:
            raise ValueError("Documento tributario obligatorio")
        return v

    @field_validator("legal_name")
    @classmethod
    def strip_legal_name(cls, v):
        if not v or not v.strip():
            raise ValueError("Razón social obligatoria")
        return v.strip()


class CustomerUpdate(BaseModel):
    legal_name: Optional[str] = None
    trade_name: Optional[str] = None
    business_activity: Optional[str] = None
    billing_email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    payment_term_days: Optional[int] = None
    credit_limit: Optional[Decimal] = None
    status: Optional[str] = None
    notes: Optional[str] = None


class CreditUpdate(BaseModel):
    credit_limit: Optional[Decimal] = None
    payment_term_days: Optional[int] = None
    credit_status: Optional[str] = None
    credit_block_reason: Optional[str] = None


class CustomerRead(BaseModel):
    id: int
    company_id: int
    code: Optional[str]
    legal_name: str
    trade_name: Optional[str]
    tax_id: str
    billing_email: Optional[str]
    phone: Optional[str]
    address: Optional[str]
    city: Optional[str]
    country: str
    payment_term_days: int
    credit_limit: Decimal
    status: str
    credit_status: str
    contacts: List[ContactRead] = []
    created_at: datetime
    model_config = {"from_attributes": True}
