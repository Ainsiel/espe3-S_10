"""schemas/inventory.py — Schemas de bodegas, stocks, movimientos y conteos."""
from datetime import datetime
from decimal import Decimal
from typing import Optional, List
from pydantic import BaseModel, field_validator


class WarehouseCreate(BaseModel):
    company_id: int = 1
    code: str
    name: str
    address: Optional[str] = None


class WarehouseRead(BaseModel):
    id: int
    code: str
    name: str
    address: Optional[str]
    status: str
    model_config = {"from_attributes": True}


class StockRead(BaseModel):
    id: int
    product_id: int
    warehouse_id: int
    location_id: Optional[int]
    physical_qty: Decimal
    reserved_qty: Decimal
    available_qty: Decimal = Decimal("0")
    model_config = {"from_attributes": True}


class MovementCreate(BaseModel):
    product_id: int
    warehouse_id: int
    location_id: Optional[int] = None
    movement_type: str
    quantity: Decimal
    unit_cost: Optional[Decimal] = None
    reason: Optional[str] = None
    source_type: Optional[str] = None
    source_id: Optional[int] = None

    @field_validator("quantity")
    @classmethod
    def positive_qty(cls, v):
        if v <= 0:
            raise ValueError("Cantidad debe ser > 0")
        return v


class MovementRead(BaseModel):
    id: int
    product_id: int
    warehouse_id: int
    movement_type: str
    quantity: Decimal
    reason: Optional[str]
    source_type: Optional[str]
    created_at: datetime
    model_config = {"from_attributes": True}


class AdjustmentCreate(BaseModel):
    company_id: int = 1
    product_id: int
    warehouse_id: int
    real_quantity: Decimal
    reason: str

    @field_validator("reason")
    @classmethod
    def reason_required(cls, v):
        if not v or not v.strip():
            raise ValueError("Motivo obligatorio en ajuste")
        return v


class TransferCreate(BaseModel):
    company_id: int = 1
    product_id: int
    from_warehouse_id: int
    to_warehouse_id: int
    quantity: Decimal
    reason: Optional[str] = None

    @field_validator("quantity")
    @classmethod
    def positive_qty(cls, v):
        if v <= 0:
            raise ValueError("Cantidad debe ser > 0")
        return v
