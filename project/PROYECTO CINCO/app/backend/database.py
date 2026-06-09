"""
database.py — Configuración SQLAlchemy + SQLite para MVP
Fábrica: fabrica-arnes-sdd-web-critica v0.1.0
Proyecto: PROYECTO_CINCO
Agente: agent.implementation
harness.run_agent("agent.implementation", state)
"""

from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from sqlalchemy.engine import Engine
import sqlite3
import os

# Base de datos SQLite para MVP local.
# Para producción: reemplazar por PostgreSQL con aprobación humana.
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./erp_proyecto_cinco.db")

connect_args = {}
if DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(DATABASE_URL, connect_args=connect_args)

# Activar WAL y foreign keys en SQLite
@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    if isinstance(dbapi_connection, sqlite3.Connection):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.close()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    """Base declarativa para todos los modelos ORM del ERP."""
    pass


def get_db():
    """Dependencia FastAPI: entrega sesión de BD y la cierra al terminar."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_tables():
    """Crea todas las tablas definidas en los modelos. Solo para MVP."""
    Base.metadata.create_all(bind=engine)
