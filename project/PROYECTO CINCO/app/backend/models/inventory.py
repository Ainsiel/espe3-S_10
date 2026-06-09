"""
models/inventory.py — Stock, movimientos, bodegas y conteos físicos.
Reglas: RN-26..40, V086-V110
Spec: especificacion_cinco.md UC-INV-03..06, J.5
"""
from datetime import datetime
from typing import Optional
from decimal import Decimal
from sqlalchemy import String, Integer, DateTime, Numeric, Text, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from database import Base


class Warehouse(Base):
    """
    Bodega. V086: Código obligatorio. V087: Código único. V089: Inactiva no acepta movimientos.
    """
    __tablename__ = "warehouses"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    company_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    code: Mapped[str] = mapped_column(String(30), nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    address: Mapped[Optional[str]] = mapped_column(String(300))
    status: Mapped[str] = mapped_column(String(20), default="active")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    locations: Mapped[list["WarehouseLocation"]] = relationship("WarehouseLocation", back_populates="warehouse")
    stocks: Mapped[list["InventoryStock"]] = relationship("InventoryStock", back_populates="warehouse")


class WarehouseLocation(Base):
    """Ubicación interna dentro de una bodega."""
    __tablename__ = "warehouse_locations"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    warehouse_id: Mapped[int] = mapped_column(Integer, ForeignKey("warehouses.id"), nullable=False)
    code: Mapped[str] = mapped_column(String(30), nullable=False)
    name: Mapped[str] = mapped_column(String(150))
    status: Mapped[str] = mapped_column(String(20), default="active")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    warehouse: Mapped["Warehouse"] = relationship("Warehouse", back_populates="locations")


class InventoryStock(Base):
    """
    Saldo de stock por producto/bodega/ubicación.
    RN-26: disponible = físico - reservado.
    RN-27: reservado <= físico.
    RN-28: No stock negativo salvo configuración.
    """
    __tablename__ = "inventory_stocks"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    product_id: Mapped[int] = mapped_column(Integer, ForeignKey("products.id"), nullable=False, index=True)
    warehouse_id: Mapped[int] = mapped_column(Integer, ForeignKey("warehouses.id"), nullable=False, index=True)
    location_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("warehouse_locations.id"))
    physical_qty: Mapped[Decimal] = mapped_column(Numeric(15, 4), default=0)
    reserved_qty: Mapped[Decimal] = mapped_column(Numeric(15, 4), default=0)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    warehouse: Mapped["Warehouse"] = relationship("Warehouse", back_populates="stocks")


class InventoryMovement(Base):
    """
    Movimiento de inventario (kardex).
    RN-30: Todo movimiento tiene tipo y motivo.
    RN-31: Afecta una bodega.
    Tipos: entrada|salida|ajuste|transferencia|produccion
    """
    __tablename__ = "inventory_movements"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    company_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    product_id: Mapped[int] = mapped_column(Integer, ForeignKey("products.id"), nullable=False)
    warehouse_id: Mapped[int] = mapped_column(Integer, ForeignKey("warehouses.id"), nullable=False)
    location_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("warehouse_locations.id"))
    # Tipos: entrada|salida|ajuste|transferencia_salida|transferencia_entrada|produccion
    movement_type: Mapped[str] = mapped_column(String(40), nullable=False)
    quantity: Mapped[Decimal] = mapped_column(Numeric(15, 4), nullable=False)
    unit_cost: Mapped[Optional[Decimal]] = mapped_column(Numeric(15, 4))
    reason: Mapped[Optional[str]] = mapped_column(String(300))
    # Trazabilidad al documento origen
    source_type: Mapped[Optional[str]] = mapped_column(String(50))
    source_id: Mapped[Optional[int]] = mapped_column(Integer)
    related_movement_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("inventory_movements.id"))
    created_by: Mapped[Optional[int]] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class InventoryCount(Base):
    """Conteo físico de inventario. RN-36: Cerrado no puede modificarse."""
    __tablename__ = "inventory_counts"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    company_id: Mapped[int] = mapped_column(Integer, nullable=False)
    warehouse_id: Mapped[int] = mapped_column(Integer, ForeignKey("warehouses.id"), nullable=False)
    responsible_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    count_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="open")  # open|approved|closed
    notes: Mapped[Optional[str]] = mapped_column(Text)
    approved_by: Mapped[Optional[int]] = mapped_column(Integer)
    approved_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    closed_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    lines: Mapped[list["InventoryCountLine"]] = relationship("InventoryCountLine", back_populates="count", cascade="all, delete-orphan")


class InventoryCountLine(Base):
    """Línea de conteo físico. V107: Cantidad >= 0. V108: Diferencia calculada automáticamente."""
    __tablename__ = "inventory_count_lines"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    count_id: Mapped[int] = mapped_column(Integer, ForeignKey("inventory_counts.id"), nullable=False)
    product_id: Mapped[int] = mapped_column(Integer, ForeignKey("products.id"), nullable=False)
    system_qty: Mapped[Decimal] = mapped_column(Numeric(15, 4), default=0)
    counted_qty: Mapped[Optional[Decimal]] = mapped_column(Numeric(15, 4))
    difference: Mapped[Optional[Decimal]] = mapped_column(Numeric(15, 4))
    count: Mapped["InventoryCount"] = relationship("InventoryCount", back_populates="lines")
