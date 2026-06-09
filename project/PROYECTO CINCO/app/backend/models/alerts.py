"""
models/alerts.py — Alertas por correo, logs de email, exportaciones y preferencias de dashboard.
Spec: especificacion_cinco.md UC-ALT-01..05, J.5
V200: Alerta requiere al menos un destinatario válido.
"""
from datetime import datetime
from typing import Optional
from sqlalchemy import String, Integer, DateTime, Text, ForeignKey, JSON, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from database import Base


class Alert(Base):
    """
    Regla de alerta por correo.
    Estados: active|paused|inactive
    Tipos: stock_low|invoice_overdue|production_late|custom
    """
    __tablename__ = "alerts"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    company_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    alert_type: Mapped[str] = mapped_column(String(50), nullable=False)
    condition: Mapped[Optional[dict]] = mapped_column(JSON)
    # V200: Al menos un destinatario válido
    recipients: Mapped[list] = mapped_column(JSON, nullable=False)
    frequency: Mapped[str] = mapped_column(String(30), default="daily")  # daily|weekly|realtime
    status: Mapped[str] = mapped_column(String(20), default="active")
    last_sent_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    created_by: Mapped[Optional[int]] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    email_logs: Mapped[list["EmailLog"]] = relationship("EmailLog", back_populates="alert")


class EmailLog(Base):
    """
    Log de envío de correo de alerta.
    Idempotencia y reintentos según UC-ALT-05.
    """
    __tablename__ = "email_logs"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    alert_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("alerts.id"))
    recipient: Mapped[str] = mapped_column(String(255), nullable=False)
    subject: Mapped[Optional[str]] = mapped_column(String(300))
    status: Mapped[str] = mapped_column(String(20), default="pending")  # pending|sent|failed|max_retries
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    last_error: Mapped[Optional[str]] = mapped_column(Text)
    sent_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    alert: Mapped[Optional["Alert"]] = relationship("Alert", back_populates="email_logs")


class ReportExport(Base):
    """Exportación de reporte. RNF-06: Registro de usuario, filtros y archivo."""
    __tablename__ = "report_exports"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    report_type: Mapped[str] = mapped_column(String(50), nullable=False)
    filters_hash: Mapped[Optional[str]] = mapped_column(String(64))
    filters: Mapped[Optional[dict]] = mapped_column(JSON)
    file_url: Mapped[Optional[str]] = mapped_column(String(500))
    status: Mapped[str] = mapped_column(String(20), default="pending")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class DashboardPreference(Base):
    """Preferencias de dashboard por usuario. UC-REP-05."""
    __tablename__ = "dashboard_preferences"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False, unique=True)
    widgets: Mapped[Optional[list]] = mapped_column(JSON)
    default_filters: Mapped[Optional[dict]] = mapped_column(JSON)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
