"""
models/customers.py — Modelos de clientes y contactos.
Reglas: RN-11..20, V036-V055
Spec source: especificacion_cinco.md UC-CLI-01..05, J.5
"""

from datetime import datetime
from typing import Optional
from decimal import Decimal
from sqlalchemy import (
    String, Boolean, Integer, DateTime, Numeric, Text, ForeignKey
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from database import Base


class Customer(Base):
    """
    Cliente comercial.
    RN-11: Documento tributario único por empresa.
    RN-12: Cliente inactivo no puede usarse en nuevas ventas.
    RN-13: Cliente bloqueado no puede facturarse sin autorización.
    RN-14: Límite de crédito evaluado contra facturas pendientes.
    V036: Razón social obligatoria.
    V038: Documento tributario único por empresa.
    """
    __tablename__ = "customers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    company_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    # V054: Código interno único por empresa
    code: Mapped[Optional[str]] = mapped_column(String(30), index=True)
    # V036: Razón social obligatoria
    legal_name: Mapped[str] = mapped_column(String(150), nullable=False)
    # V039: Nombre comercial máximo 150 caracteres
    trade_name: Mapped[Optional[str]] = mapped_column(String(150))
    # V037: Documento tributario obligatorio
    tax_id: Mapped[str] = mapped_column(String(30), nullable=False, index=True)
    business_activity: Mapped[Optional[str]] = mapped_column(String(200))
    # V040-V041: Correo facturación
    billing_email: Mapped[Optional[str]] = mapped_column(String(255))
    phone: Mapped[Optional[str]] = mapped_column(String(30))
    # V042-V044: Dirección obligatoria
    address: Mapped[Optional[str]] = mapped_column(String(300))
    city: Mapped[Optional[str]] = mapped_column(String(100))
    country: Mapped[str] = mapped_column(String(60), default="Chile")
    # V047: Plazo de pago >= 0
    payment_term_days: Mapped[int] = mapped_column(Integer, default=0)
    # V046: Límite de crédito >= 0
    credit_limit: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=0)
    # V045: Estado activo | inactivo | bloqueado
    status: Mapped[str] = mapped_column(String(20), default="active", nullable=False)
    # V048: Bloqueado requiere motivo
    credit_status: Mapped[str] = mapped_column(String(20), default="ok")
    credit_block_reason: Mapped[Optional[str]] = mapped_column(String(300))
    notes: Mapped[Optional[str]] = mapped_column(Text)
    created_by: Mapped[Optional[int]] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relaciones
    contacts: Mapped[list["CustomerContact"]] = relationship(
        "CustomerContact", back_populates="customer", cascade="all, delete-orphan"
    )


class CustomerContact(Base):
    """
    Contacto de cliente.
    V049: Requiere nombre.
    V050: Requiere correo o teléfono.
    V051: Solo un contacto principal por cliente.
    """
    __tablename__ = "customer_contacts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    customer_id: Mapped[int] = mapped_column(Integer, ForeignKey("customers.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    position: Mapped[Optional[str]] = mapped_column(String(100))
    email: Mapped[Optional[str]] = mapped_column(String(255))
    phone: Mapped[Optional[str]] = mapped_column(String(30))
    # V051: Solo un is_primary=True por cliente
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relaciones
    customer: Mapped["Customer"] = relationship("Customer", back_populates="contacts")
