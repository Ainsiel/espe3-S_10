"""
models/products.py — Productos, categorías y unidades de medida.
Reglas: RN-21..25, V066-V085
Spec: especificacion_cinco.md UC-INV-01..02, J.5
"""
from datetime import datetime
from typing import Optional
from decimal import Decimal
from sqlalchemy import String, Boolean, Integer, DateTime, Numeric, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from database import Base


class ProductCategory(Base):
    """Categoría de producto. V069: Categoría obligatoria."""
    __tablename__ = "product_categories"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    company_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="active")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    products: Mapped[list["Product"]] = relationship("Product", back_populates="category")


class Unit(Base):
    """Unidad de medida. V070: Unidad base obligatoria."""
    __tablename__ = "units"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    company_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(60), nullable=False)
    symbol: Mapped[str] = mapped_column(String(10), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="active")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    products: Mapped[list["Product"]] = relationship("Product", back_populates="unit")


class Product(Base):
    """
    Producto maestro del ERP.
    RN-21: SKU único por empresa.
    RN-22: Producto inactivo no puede venderse ni comprarse.
    RN-23: Sin control stock → no genera movimientos.
    RN-24: Con control stock → requiere unidad base.
    RN-25: Unidad base no cambia si hay movimientos.
    V066: SKU obligatorio. V067: SKU único. V068: Nombre obligatorio.
    V071: Precio venta >= 0. V072: Costo >= 0. V073: Stock mín >= 0.
    """
    __tablename__ = "products"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    company_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    sku: Mapped[str] = mapped_column(String(60), nullable=False, unique=True, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    category_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("product_categories.id"))
    unit_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("units.id"))
    barcode: Mapped[Optional[str]] = mapped_column(String(80), unique=True)
    # V071-V072
    sale_price: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=0)
    cost: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=0)
    tax_rate: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=19.00)
    # V073: stock_min >= 0
    min_stock: Mapped[Decimal] = mapped_column(Numeric(15, 4), default=0)
    # RN-23: controla_inventario
    track_stock: Mapped[bool] = mapped_column(Boolean, default=True)
    # RN-81: marcado como producible
    is_producible: Mapped[bool] = mapped_column(Boolean, default=False)
    is_purchasable: Mapped[bool] = mapped_column(Boolean, default=True)
    status: Mapped[str] = mapped_column(String(20), default="active")
    created_by: Mapped[Optional[int]] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    category: Mapped[Optional["ProductCategory"]] = relationship("ProductCategory", back_populates="products")
    unit: Mapped[Optional["Unit"]] = relationship("Unit", back_populates="products")
