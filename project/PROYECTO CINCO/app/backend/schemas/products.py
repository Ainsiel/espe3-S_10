"""schemas/products.py — Schemas de productos, categorías y unidades."""
from datetime import datetime
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, field_validator


class CategoryCreate(BaseModel):
    company_id: int = 1
    name: str


class CategoryRead(BaseModel):
    id: int
    name: str
    status: str
    model_config = {"from_attributes": True}


class UnitCreate(BaseModel):
    company_id: int = 1
    name: str
    symbol: str


class UnitRead(BaseModel):
    id: int
    name: str
    symbol: str
    status: str
    model_config = {"from_attributes": True}


class ProductCreate(BaseModel):
    company_id: int = 1
    sku: str
    name: str
    description: Optional[str] = None
    category_id: Optional[int] = None
    unit_id: Optional[int] = None
    barcode: Optional[str] = None
    sale_price: Decimal = Decimal("0")
    cost: Decimal = Decimal("0")
    tax_rate: Decimal = Decimal("19.00")
    min_stock: Decimal = Decimal("0")
    track_stock: bool = True
    is_producible: bool = False
    is_purchasable: bool = True

    @field_validator("sku")
    @classmethod
    def strip_sku(cls, v):
        v = v.strip()
        if not v:
            raise ValueError("SKU obligatorio")
        return v

    @field_validator("sale_price", "cost", "min_stock")
    @classmethod
    def non_negative(cls, v):
        if v < 0:
            raise ValueError("Valor debe ser >= 0")
        return v


class ProductUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    category_id: Optional[int] = None
    barcode: Optional[str] = None
    sale_price: Optional[Decimal] = None
    cost: Optional[Decimal] = None
    tax_rate: Optional[Decimal] = None
    min_stock: Optional[Decimal] = None
    is_producible: Optional[bool] = None
    is_purchasable: Optional[bool] = None
    status: Optional[str] = None


class ProductRead(BaseModel):
    id: int
    company_id: int
    sku: str
    name: str
    description: Optional[str]
    category_id: Optional[int]
    unit_id: Optional[int]
    barcode: Optional[str]
    sale_price: Decimal
    cost: Decimal
    tax_rate: Decimal
    min_stock: Decimal
    track_stock: bool
    is_producible: bool
    is_purchasable: bool
    status: str
    category: Optional[CategoryRead] = None
    unit: Optional[UnitRead] = None
    created_at: datetime
    model_config = {"from_attributes": True}
