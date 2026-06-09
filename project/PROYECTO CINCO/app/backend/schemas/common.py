"""
schemas/common.py — Schemas comunes: respuestas, paginación y errores.
Contrato API J.7: formato unificado de respuesta y error.
"""
from typing import Any, Generic, List, Optional, TypeVar
from pydantic import BaseModel

T = TypeVar("T")


class Meta(BaseModel):
    request_id: Optional[str] = None
    timestamp: Optional[str] = None
    total: Optional[int] = None
    page: Optional[int] = None
    page_size: Optional[int] = None


class DataResponse(BaseModel, Generic[T]):
    """Formato de respuesta exitosa: { data: T, meta: Meta }"""
    data: T
    meta: Meta = Meta()


class ErrorDetail(BaseModel):
    field: Optional[str] = None
    issue: str


class ErrorResponse(BaseModel):
    """Formato de error: { error: { code, message, details }, meta }"""
    class ErrorBody(BaseModel):
        code: str
        message: str
        details: List[ErrorDetail] = []

    error: ErrorBody
    meta: Meta = Meta()


class PaginationParams(BaseModel):
    page: int = 1
    page_size: int = 20
    search: Optional[str] = None
