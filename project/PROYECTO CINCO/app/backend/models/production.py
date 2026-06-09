"""
models/production.py — Recetas BOM, órdenes de producción y consumos.
Reglas: RN-81..90, V171-V190
Spec: especificacion_cinco.md UC-PROD-01..05, J.5
"""
from datetime import datetime
from typing import Optional
from decimal import Decimal
from sqlalchemy import String, Integer, DateTime, Numeric, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from database import Base


class ProductionBOM(Base):
    """
    Receta de producción (Bill of Materials) versionada.
    RN-82: Producto terminado debe tener receta activa.
    RN-83: Receta debe tener al menos un insumo.
    V171-V177.
    """
    __tablename__ = "production_boms"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    company_id: Mapped[int] = mapped_column(Integer, nullable=False)
    product_id: Mapped[int] = mapped_column(Integer, ForeignKey("products.id"), nullable=False)
    version: Mapped[str] = mapped_column(String(20), nullable=False)
    # RN-87: Merma estándar
    standard_waste_pct: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=0)
    status: Mapped[str] = mapped_column(String(20), default="draft")  # draft|active|inactive
    notes: Mapped[Optional[str]] = mapped_column(Text)
    created_by: Mapped[Optional[int]] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    lines: Mapped[list["ProductionBOMLine"]] = relationship("ProductionBOMLine", back_populates="bom", cascade="all, delete-orphan")
    orders: Mapped[list["ProductionOrder"]] = relationship("ProductionOrder", back_populates="bom")


class ProductionBOMLine(Base):
    """
    Insumo de receta.
    RN-84: Producto no puede ser insumo de sí mismo.
    V174: Insumo requiere producto. V175: Cantidad > 0. V176: No auto-insumo.
    """
    __tablename__ = "production_bom_lines"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    bom_id: Mapped[int] = mapped_column(Integer, ForeignKey("production_boms.id"), nullable=False)
    # RN-84: component_product_id != bom.product_id
    component_product_id: Mapped[int] = mapped_column(Integer, ForeignKey("products.id"), nullable=False)
    unit_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("units.id"))
    quantity: Mapped[Decimal] = mapped_column(Numeric(15, 4), nullable=False)
    waste_pct: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=0)
    bom: Mapped["ProductionBOM"] = relationship("ProductionBOM", back_populates="lines")


class ProductionOrder(Base):
    """
    Orden de producción.
    Estados: planned|released|in_process|partially_completed|completed|closed|cancelled
    RN-81..90, V178-V189.
    """
    __tablename__ = "production_orders"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    company_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    product_id: Mapped[int] = mapped_column(Integer, ForeignKey("products.id"), nullable=False)
    bom_id: Mapped[int] = mapped_column(Integer, ForeignKey("production_boms.id"), nullable=False)
    warehouse_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("warehouses.id"))
    number: Mapped[Optional[str]] = mapped_column(String(30), unique=True)
    status: Mapped[str] = mapped_column(String(30), default="planned")
    planned_qty: Mapped[Decimal] = mapped_column(Numeric(15, 4), nullable=False)
    produced_qty: Mapped[Decimal] = mapped_column(Numeric(15, 4), default=0)
    waste_qty: Mapped[Decimal] = mapped_column(Numeric(15, 4), default=0)
    required_date: Mapped[Optional[datetime]] = mapped_column(DateTime)
    released_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    closed_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    # RN-90: Costo real calculado al cerrar
    real_cost: Mapped[Optional[Decimal]] = mapped_column(Numeric(15, 2))
    notes: Mapped[Optional[str]] = mapped_column(Text)
    created_by: Mapped[Optional[int]] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    bom: Mapped["ProductionBOM"] = relationship("ProductionBOM", back_populates="orders")
    consumptions: Mapped[list["ProductionConsumption"]] = relationship("ProductionConsumption", back_populates="order", cascade="all, delete-orphan")


class ProductionConsumption(Base):
    """
    Consumo real de insumos en orden de producción.
    RN-85: Liberación consume insumos.
    V183-V184: Cantidades >= 0.
    RN-88: Orden cerrada no admite nuevos consumos.
    """
    __tablename__ = "production_consumptions"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    production_order_id: Mapped[int] = mapped_column(Integer, ForeignKey("production_orders.id"), nullable=False)
    product_id: Mapped[int] = mapped_column(Integer, ForeignKey("products.id"), nullable=False)
    bom_line_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("production_bom_lines.id"))
    required_qty: Mapped[Decimal] = mapped_column(Numeric(15, 4), nullable=False)
    consumed_qty: Mapped[Decimal] = mapped_column(Numeric(15, 4), default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    order: Mapped["ProductionOrder"] = relationship("ProductionOrder", back_populates="consumptions")
