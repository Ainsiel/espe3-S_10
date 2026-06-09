"""schemas/production.py — Schemas de producción."""
from datetime import datetime
from decimal import Decimal
from typing import Optional, List
from pydantic import BaseModel, field_validator


class BOMLineCreate(BaseModel):
    component_product_id: int
    unit_id: Optional[int] = None
    quantity: Decimal
    waste_pct: Decimal = Decimal("0")


class BOMCreate(BaseModel):
    company_id: int = 1
    product_id: int
    version: str
    standard_waste_pct: Decimal = Decimal("0")
    notes: Optional[str] = None
    lines: List[BOMLineCreate]

    @field_validator("lines")
    @classmethod
    def at_least_one(cls, v):
        if not v:
            raise ValueError("Receta requiere al menos un insumo")
        return v


class BOMRead(BaseModel):
    id: int
    product_id: int
    version: str
    status: str
    standard_waste_pct: Decimal
    created_at: datetime
    model_config = {"from_attributes": True}


class ProductionOrderCreate(BaseModel):
    company_id: int = 1
    product_id: int
    bom_id: int
    warehouse_id: Optional[int] = None
    planned_qty: Decimal
    required_date: Optional[datetime] = None
    notes: Optional[str] = None

    @field_validator("planned_qty")
    @classmethod
    def positive(cls, v):
        if v <= 0:
            raise ValueError("Cantidad planificada debe ser > 0")
        return v


class ProductionOutputReport(BaseModel):
    produced_qty: Decimal
    waste_qty: Decimal = Decimal("0")
    notes: Optional[str] = None


class ProductionOrderRead(BaseModel):
    id: int
    product_id: int
    bom_id: int
    number: Optional[str]
    status: str
    planned_qty: Decimal
    produced_qty: Decimal
    waste_qty: Decimal
    required_date: Optional[datetime]
    created_at: datetime
    model_config = {"from_attributes": True}
