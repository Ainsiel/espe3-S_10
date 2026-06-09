"""schemas/purchases.py — Schemas de proveedores y compras."""
from datetime import datetime
from decimal import Decimal
from typing import Optional, List
from pydantic import BaseModel


class SupplierCreate(BaseModel):
    company_id: int = 1
    tax_id: str
    legal_name: str
    trade_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    country: str = "Chile"
    payment_term_days: int = 30


class SupplierRead(BaseModel):
    id: int
    tax_id: str
    legal_name: str
    email: Optional[str]
    status: str
    created_at: datetime
    model_config = {"from_attributes": True}


class PurchaseOrderLineCreate(BaseModel):
    product_id: int
    quantity: Decimal
    unit_price: Decimal
    tax_rate: Decimal = Decimal("19")


class PurchaseOrderCreate(BaseModel):
    company_id: int = 1
    supplier_id: int
    required_date: Optional[datetime] = None
    notes: Optional[str] = None
    lines: List[PurchaseOrderLineCreate]


class PurchaseOrderRead(BaseModel):
    id: int
    supplier_id: int
    number: Optional[str]
    status: str
    total: Decimal
    created_at: datetime
    model_config = {"from_attributes": True}


class GoodsReceiptLineCreate(BaseModel):
    purchase_order_line_id: int
    product_id: int
    quantity: Decimal


class GoodsReceiptCreate(BaseModel):
    purchase_order_id: int
    warehouse_id: int
    notes: Optional[str] = None
    lines: List[GoodsReceiptLineCreate]


class SupplierInvoiceCreate(BaseModel):
    company_id: int = 1
    supplier_id: int
    purchase_order_id: Optional[int] = None
    goods_receipt_id: Optional[int] = None
    number: str
    issued_at: datetime
    net_amount: Decimal
    tax_amount: Decimal = Decimal("0")
    total: Decimal
    due_date: Optional[datetime] = None
