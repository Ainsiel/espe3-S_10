"""
models/auth.py — Modelos de autenticación, usuarios, roles y auditoría.
Reglas: V019-V035, RNF-01, RNF-02
Spec source: especificacion_cinco.md sección H, J.5
"""

from datetime import datetime
from typing import Optional
from sqlalchemy import (
    String, Boolean, Integer, DateTime, Text, ForeignKey, JSON
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from database import Base


class Role(Base):
    """
    Rol de usuario. Agrupa permisos.
    V025: Rol obligatorio para usuario activo.
    V026: Rol inactivo no puede asignarse.
    """
    __tablename__ = "roles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    company_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(300))
    status: Mapped[str] = mapped_column(String(20), default="active", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relaciones
    permissions: Mapped[list["RolePermission"]] = relationship("RolePermission", back_populates="role", cascade="all, delete-orphan")
    users: Mapped[list["User"]] = relationship("User", back_populates="role")


class RolePermission(Base):
    """
    Permiso asignado a un rol (modelo RBAC).
    Permisos: customers.read, customers.create, ... (ver spec sección H)
    """
    __tablename__ = "role_permissions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    role_id: Mapped[int] = mapped_column(Integer, ForeignKey("roles.id"), nullable=False)
    permission_code: Mapped[str] = mapped_column(String(100), nullable=False)

    # Relaciones
    role: Mapped["Role"] = relationship("Role", back_populates="permissions")


class User(Base):
    """
    Usuario del sistema.
    V019: Usuario debe estar autenticado.
    V020: Usuario debe estar activo.
    V021: Correo único por empresa.
    V022: Contraseña mínima 8 caracteres (validado en schema).
    V023: Contraseña almacenada con hash bcrypt.
    V024: Usuario bloqueado no puede iniciar sesión.
    """
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    company_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(200), nullable=False)
    role_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("roles.id"))
    status: Mapped[str] = mapped_column(String(20), default="active", nullable=False)
    # V033: Sesión registra IP
    last_ip: Mapped[Optional[str]] = mapped_column(String(45))
    # V034: Intentos fallidos de login
    failed_login_attempts: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relaciones
    role: Mapped[Optional["Role"]] = relationship("Role", back_populates="users")
    audit_logs: Mapped[list["AuditLog"]] = relationship("AuditLog", back_populates="actor")


class AuditLog(Base):
    """
    Historial de acciones críticas del sistema.
    RNF-02: 100% de cambios críticos con actor, fecha, antes/después e IP.
    """
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    actor_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("users.id"))
    entity: Mapped[str] = mapped_column(String(100), nullable=False)
    entity_id: Mapped[Optional[str]] = mapped_column(String(50))
    action: Mapped[str] = mapped_column(String(50), nullable=False)
    before_data: Mapped[Optional[dict]] = mapped_column(JSON)
    after_data: Mapped[Optional[dict]] = mapped_column(JSON)
    ip_address: Mapped[Optional[str]] = mapped_column(String(45))
    user_agent: Mapped[Optional[str]] = mapped_column(String(500))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relaciones
    actor: Mapped[Optional["User"]] = relationship("User", back_populates="audit_logs")
