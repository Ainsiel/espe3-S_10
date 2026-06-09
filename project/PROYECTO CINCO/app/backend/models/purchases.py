"""
models/purchases.py — Proveedores, órdenes de compra, recepciones y facturas.
Reglas: RN-71..80, V151-V170
Spec: especificacion_cinco.md UC-COM-01..05, J.5
"""
from datetime import datetime
from typing import Optional
from decimal import Decimal
from sqlalchemy import String, Integer, DateTime, Numeric, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from database import Base


class Supplier(Base):
    """
    Proveedor. RN-71: Documento tributario único por empresa.
    RN-72: Proveedor inactivo no puede recibir órdenes.
    V056-V065.
    """
    __tablename__ = "suppliers"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    company_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    tax_id: Mapped[str] = mapped_column(String(30), nullable=False, index=True)
    legal_name: Mapped[str] = mapped_column(String(150), nullable=False)
    trade_name: Mapped[Optional[str]] = mapped_column(String(150))
    email: Mapped[Optional[str]] = mapped_column(String(255))
    phone: Mapped[Optional[str]] = mapped_column(String(30))
    address: Mapped[Optional[str]] = mapped_column(String(300))
    city: Mapped[Optional[str]] = mapped_column(String(100))
    country: Mapped[str] = mapped_column(String(60), default="Chile")
    payment_term_days: Mapped[int] = mapped_column(Integer, default=30)
    status: Mapped[str] = mapped_column(String(20), default="active")
    notes: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    contacts: Mapped[list["SupplierContact"]] = relationship("SupplierContact", back_populates="supplier", cascade="all, delete-orphan")
    purchase_orders: Mapped[list["PurchaseOrder"]] = relationship("PurchaseOrder", back_populates="supplier")


class SupplierContact(Base):
    __tablename__ = "supplier_contacts"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    supplier_id: Mapped[int] = mapped_column(Integer, ForeignKey("suppliers.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    position: Mapped[Optional[str]] = mapped_column(String(100))
    email: Mapped[Optional[str]] = mapped_column(String(255))
    phone: Mapped[Optional[str]] = mapped_column(String(30))
    is_primary: Mapped[bool] = mapped_column(Integer, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    supplier: Mapped["Supplier"] = relationship("Supplier", back_populates="contacts")


class PurchaseOrder(Base):
    """
    Orden de compra.
    Estados: draft|issued|approved|partially_received|received|cancelled
    RN-73..78, V151-V168.
    """
    __tablename__ = "purchase_orders"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    company_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    supplier_id: Mapped[int] = mapped_column(Integer, ForeignKey("suppliers.id"), nullable=False)
    number: Mapped[Optional[str]] = mapped_column(String(30), unique=True)
    status: Mapped[str] = mapped_column(String(30), default="draft")
    order_date: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    required_date: Mapped[Optional[datetime]] = mapped_column(DateTime)
    subtotal: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=0)
    tax_total: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=0)
    total: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=0)
    notes: Mapped[Optional[str]] = mapped_column(Text)
    approved_by: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("users.id"))
    approved_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    created_by: Mapped[Optional[int]] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    supplier: Mapped["Supplier"] = relationship("Supplier", back_populates="purchase_orders")
    lines: Mapped[list["PurchaseOrderLine"]] = relationship("PurchaseOrderLine", back_populates="order", cascade="all, delete-orphan")
    receipts: Mapped[list["GoodsReceipt"]] = relationship("GoodsReceipt", back_populates="order")


class PurchaseOrderLine(Base):
    """Línea de compra. V154-V156."""
    __tablename__ = "purchase_order_lines"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    purchase_order_id: Mapped[int] = mapped_column(Integer, ForeignKey("purchase_orders.id"), nullable=False)
    product_id: Mapped[int] = mapped_column(Integer, ForeignKey("products.id"), nullable=False)
    quantity: Mapped[Decimal] = mapped_column(Numeric(15, 4), nullable=False)
    received_qty: Mapped[Decimal] = mapped_column(Numeric(15, 4), default=0)
    unit_price: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    tax_rate: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=19)
    subtotal: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=0)
    order: Mapped["PurchaseOrder"] = relationship("PurchaseOrder", back_populates="lines")


class GoodsReceipt(Base):
    """Recepción de mercadería. V158-V161."""
    __tablename__ = "goods_receipts"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    purchase_order_id: Mapped[int] = mapped_column(Integer, ForeignKey("purchase_orders.id"), nullable=False)
    warehouse_id: Mapped[int] = mapped_column(Integer, ForeignKey("warehouses.id"), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="draft")
    received_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    notes: Mapped[Optional[str]] = mapped_column(Text)
    created_by: Mapped[Optional[int]] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    order: Mapped["PurchaseOrder"] = relationship("PurchaseOrder", back_populates="receipts")
    lines: Mapped[list["GoodsReceiptLine"]] = relationship("GoodsReceiptLine", back_populates="receipt", cascade="all, delete-orphan")


class GoodsReceiptLine(Base):
    __tablename__ = "goods_receipt_lines"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    receipt_id: Mapped[int] = mapped_column(Integer, ForeignKey("goods_receipts.id"), nullable=False)
    purchase_order_line_id: Mapped[int] = mapped_column(Integer, ForeignKey("purchase_order_lines.id"), nullable=False)
    product_id: Mapped[int] = mapped_column(Integer, ForeignKey("products.id"), nullable=False)
    quantity: Mapped[Decimal] = mapped_column(Numeric(15, 4), nullable=False)
    receipt: Mapped["GoodsReceipt"] = relationship("GoodsReceipt", back_populates="lines")


class SupplierInvoice(Base):
    """
    Factura de compra.
    RN-79..80, V162-V167.
    RN-80: Factura no puede duplicarse por proveedor y número.
    """
    __tablename__ = "supplier_invoices"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    company_id: Mapped[int] = mapped_column(Integer, nullable=False)
    supplier_id: Mapped[int] = mapped_column(Integer, ForeignKey("suppliers.id"), nullable=False)
    purchase_order_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("purchase_orders.id"))
    goods_receipt_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("goods_receipts.id"))
    number: Mapped[str] = mapped_column(String(50), nullable=False)
    issued_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    net_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    tax_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=0)
    total: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="pending")
    due_date: Mapped[Optional[datetime]] = mapped_column(DateTime)
    created_by: Mapped[Optional[int]] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
