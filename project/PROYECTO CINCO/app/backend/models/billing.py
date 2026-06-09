"""
models/billing.py — Facturas, notas de crédito/débito y pagos.
Reglas: RN-91..100, V191-V200
Spec: especificacion_cinco.md UC-FAC-01..05, J.5
"""
from datetime import datetime
from typing import Optional
from decimal import Decimal
from sqlalchemy import String, Integer, DateTime, Numeric, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from database import Base


class Invoice(Base):
    """
    Factura de venta.
    Estados: draft|issued|partially_paid|paid|cancelled|credited
    RN-91..100. V191-V200.
    """
    __tablename__ = "invoices"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    company_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    customer_id: Mapped[int] = mapped_column(Integer, ForeignKey("customers.id"), nullable=False)
    sales_order_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("sales_orders.id"))
    # V100: Número único
    number: Mapped[str] = mapped_column(String(30), nullable=False, unique=True)
    status: Mapped[str] = mapped_column(String(30), default="draft")
    issued_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    due_date: Mapped[Optional[datetime]] = mapped_column(DateTime)
    # V195: neto + impuestos = total
    net_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    tax_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=0)
    total: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    balance: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(Text)
    created_by: Mapped[Optional[int]] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    lines: Mapped[list["InvoiceLine"]] = relationship("InvoiceLine", back_populates="invoice", cascade="all, delete-orphan")
    payments: Mapped[list["Payment"]] = relationship("Payment", back_populates="invoice")
    credit_notes: Mapped[list["CreditNote"]] = relationship("CreditNote", back_populates="invoice")
    debit_notes: Mapped[list["DebitNote"]] = relationship("DebitNote", back_populates="invoice")


class InvoiceLine(Base):
    __tablename__ = "invoice_lines"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    invoice_id: Mapped[int] = mapped_column(Integer, ForeignKey("invoices.id"), nullable=False)
    product_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("products.id"))
    description: Mapped[str] = mapped_column(String(300), nullable=False)
    quantity: Mapped[Decimal] = mapped_column(Numeric(15, 4), nullable=False)
    unit_price: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    discount_pct: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=0)
    tax_rate: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=19)
    subtotal: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    invoice: Mapped["Invoice"] = relationship("Invoice", back_populates="lines")


class CreditNote(Base):
    """
    Nota de crédito.
    RN-95: Asociada a factura original.
    RN-96: No puede superar saldo facturado.
    V196-V197.
    """
    __tablename__ = "credit_notes"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    invoice_id: Mapped[int] = mapped_column(Integer, ForeignKey("invoices.id"), nullable=False)
    sales_return_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("sales_returns.id"))
    number: Mapped[str] = mapped_column(String(30), nullable=False, unique=True)
    reason: Mapped[str] = mapped_column(String(300), nullable=False)
    total: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="issued")
    issued_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    created_by: Mapped[Optional[int]] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    invoice: Mapped["Invoice"] = relationship("Invoice", back_populates="credit_notes")


class DebitNote(Base):
    """Nota de débito. RN-97: Concepto obligatorio."""
    __tablename__ = "debit_notes"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    invoice_id: Mapped[int] = mapped_column(Integer, ForeignKey("invoices.id"), nullable=False)
    number: Mapped[str] = mapped_column(String(30), nullable=False, unique=True)
    concept: Mapped[str] = mapped_column(String(300), nullable=False)
    total: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    tax_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=0)
    status: Mapped[str] = mapped_column(String(20), default="issued")
    issued_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    created_by: Mapped[Optional[int]] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    invoice: Mapped["Invoice"] = relationship("Invoice", back_populates="debit_notes")


class Payment(Base):
    """
    Pago de factura.
    RN-98: No puede superar saldo salvo anticipo.
    RN-99: Factura pagada → cerrada financieramente.
    V198-V199.
    """
    __tablename__ = "payments"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    invoice_id: Mapped[int] = mapped_column(Integer, ForeignKey("invoices.id"), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    method: Mapped[str] = mapped_column(String(40), nullable=False)  # transfer|cash|check|card
    reference: Mapped[Optional[str]] = mapped_column(String(100))
    payment_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="applied")
    created_by: Mapped[Optional[int]] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    invoice: Mapped["Invoice"] = relationship("Invoice", back_populates="payments")
