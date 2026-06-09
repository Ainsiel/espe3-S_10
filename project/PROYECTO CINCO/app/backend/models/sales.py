"""
models/sales.py — Cotizaciones, órdenes de venta, despachos y devoluciones.
Reglas: RN-41..70, V111-V150
Spec: especificacion_cinco.md UC-VTA-01..05, UC-DEV-01..05, J.5
"""
from datetime import datetime
from typing import Optional
from decimal import Decimal
from sqlalchemy import String, Integer, DateTime, Numeric, Text, ForeignKey, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from database import Base


class Quotation(Base):
    """
    Cotización de venta.
    Estados: draft|issued|expired|converted|cancelled
    RN-56: Cotización vencida no puede convertirse.
    RN-57: Cotización convertida no puede volver a convertirse.
    """
    __tablename__ = "quotations"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    company_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    customer_id: Mapped[int] = mapped_column(Integer, ForeignKey("customers.id"), nullable=False)
    number: Mapped[Optional[str]] = mapped_column(String(30), unique=True)
    status: Mapped[str] = mapped_column(String(30), default="draft")
    # V126: Cotización requiere fecha de vencimiento
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    subtotal: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=0)
    tax_total: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=0)
    total: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=0)
    notes: Mapped[Optional[str]] = mapped_column(Text)
    seller_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("users.id"))
    created_by: Mapped[Optional[int]] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    lines: Mapped[list["QuotationLine"]] = relationship("QuotationLine", back_populates="quotation", cascade="all, delete-orphan")


class QuotationLine(Base):
    __tablename__ = "quotation_lines"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    quotation_id: Mapped[int] = mapped_column(Integer, ForeignKey("quotations.id"), nullable=False)
    product_id: Mapped[int] = mapped_column(Integer, ForeignKey("products.id"), nullable=False)
    quantity: Mapped[Decimal] = mapped_column(Numeric(15, 4), nullable=False)
    unit_price: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    discount_pct: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=0)
    tax_rate: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=19)
    subtotal: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=0)
    quotation: Mapped["Quotation"] = relationship("Quotation", back_populates="lines")


class SalesOrder(Base):
    """
    Orden de venta.
    Estados: draft|confirmed|partially_dispatched|dispatched|invoiced|cancelled
    RN-41..60: Reglas de venta completas.
    V111-V135.
    """
    __tablename__ = "sales_orders"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    company_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    customer_id: Mapped[int] = mapped_column(Integer, ForeignKey("customers.id"), nullable=False)
    quotation_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("quotations.id"))
    number: Mapped[Optional[str]] = mapped_column(String(30), unique=True)
    status: Mapped[str] = mapped_column(String(30), default="draft")
    order_date: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    delivery_date: Mapped[Optional[datetime]] = mapped_column(DateTime)
    payment_term_days: Mapped[int] = mapped_column(Integer, default=0)
    # RN-48: reserva stock al confirmar
    stock_reserved: Mapped[bool] = mapped_column(Boolean, default=False)
    subtotal: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=0)
    discount_total: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=0)
    tax_total: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=0)
    total: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=0)
    notes: Mapped[Optional[str]] = mapped_column(Text)
    seller_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("users.id"))
    created_by: Mapped[Optional[int]] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    lines: Mapped[list["SalesOrderLine"]] = relationship("SalesOrderLine", back_populates="order", cascade="all, delete-orphan")
    dispatches: Mapped[list["SalesDispatch"]] = relationship("SalesDispatch", back_populates="order")
    returns: Mapped[list["SalesReturn"]] = relationship("SalesReturn", back_populates="order")


class SalesOrderLine(Base):
    """Línea de venta. V115-V120."""
    __tablename__ = "sales_order_lines"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    sales_order_id: Mapped[int] = mapped_column(Integer, ForeignKey("sales_orders.id"), nullable=False)
    product_id: Mapped[int] = mapped_column(Integer, ForeignKey("products.id"), nullable=False)
    quantity: Mapped[Decimal] = mapped_column(Numeric(15, 4), nullable=False)
    dispatched_qty: Mapped[Decimal] = mapped_column(Numeric(15, 4), default=0)
    unit_price: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    discount_pct: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=0)
    tax_rate: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=19)
    subtotal: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=0)
    order: Mapped["SalesOrder"] = relationship("SalesOrder", back_populates="lines")


class SalesDispatch(Base):
    """Despacho de venta. V129-V132."""
    __tablename__ = "sales_dispatches"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    sales_order_id: Mapped[int] = mapped_column(Integer, ForeignKey("sales_orders.id"), nullable=False)
    warehouse_id: Mapped[int] = mapped_column(Integer, ForeignKey("warehouses.id"), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="draft")
    dispatched_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    notes: Mapped[Optional[str]] = mapped_column(Text)
    created_by: Mapped[Optional[int]] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    order: Mapped["SalesOrder"] = relationship("SalesOrder", back_populates="dispatches")
    lines: Mapped[list["SalesDispatchLine"]] = relationship("SalesDispatchLine", back_populates="dispatch", cascade="all, delete-orphan")


class SalesDispatchLine(Base):
    __tablename__ = "sales_dispatch_lines"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    dispatch_id: Mapped[int] = mapped_column(Integer, ForeignKey("sales_dispatches.id"), nullable=False)
    sales_order_line_id: Mapped[int] = mapped_column(Integer, ForeignKey("sales_order_lines.id"), nullable=False)
    product_id: Mapped[int] = mapped_column(Integer, ForeignKey("products.id"), nullable=False)
    quantity: Mapped[Decimal] = mapped_column(Numeric(15, 4), nullable=False)
    dispatch: Mapped["SalesDispatch"] = relationship("SalesDispatch", back_populates="lines")


class SalesReturn(Base):
    """
    Devolución de venta.
    Estados: requested|approved|rejected|received|credited|closed
    RN-61..70, V136-V150.
    """
    __tablename__ = "sales_returns"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    company_id: Mapped[int] = mapped_column(Integer, nullable=False)
    sales_order_id: Mapped[int] = mapped_column(Integer, ForeignKey("sales_orders.id"), nullable=False)
    customer_id: Mapped[int] = mapped_column(Integer, ForeignKey("customers.id"), nullable=False)
    # V138: Motivo obligatorio
    reason: Mapped[str] = mapped_column(String(300), nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="requested")
    approved_by: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("users.id"))
    approved_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    rejection_reason: Mapped[Optional[str]] = mapped_column(String(300))
    total: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=0)
    created_by: Mapped[Optional[int]] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    order: Mapped["SalesOrder"] = relationship("SalesOrder", back_populates="returns")
    lines: Mapped[list["SalesReturnLine"]] = relationship("SalesReturnLine", back_populates="return_order", cascade="all, delete-orphan")


class SalesReturnLine(Base):
    """Línea de devolución. V140-V143."""
    __tablename__ = "sales_return_lines"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    return_id: Mapped[int] = mapped_column(Integer, ForeignKey("sales_returns.id"), nullable=False)
    product_id: Mapped[int] = mapped_column(Integer, ForeignKey("products.id"), nullable=False)
    sales_order_line_id: Mapped[int] = mapped_column(Integer, ForeignKey("sales_order_lines.id"), nullable=False)
    quantity: Mapped[Decimal] = mapped_column(Numeric(15, 4), nullable=False)
    received_qty: Mapped[Optional[Decimal]] = mapped_column(Numeric(15, 4))
    # Condición: ok|damaged|waste|review
    condition: Mapped[Optional[str]] = mapped_column(String(20))
    unit_price: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=0)
    return_order: Mapped["SalesReturn"] = relationship("SalesReturn", back_populates="lines")
