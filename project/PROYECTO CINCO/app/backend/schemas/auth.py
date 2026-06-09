"""schemas/auth.py — Schemas de autenticación y usuarios."""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, field_validator


class LoginRequest(BaseModel):
    email: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    refresh_token: str


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str

    @field_validator("new_password")
    @classmethod
    def password_min_length(cls, v):
        if len(v) < 8:
            raise ValueError("Contraseña mínima de 8 caracteres")
        return v


class UserCreate(BaseModel):
    company_id: int = 1
    email: str
    password: str
    full_name: str
    role_id: Optional[int] = None

    @field_validator("password")
    @classmethod
    def password_min_length(cls, v):
        if len(v) < 8:
            raise ValueError("Contraseña mínima de 8 caracteres")
        return v


class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    role_id: Optional[int] = None
    status: Optional[str] = None


class UserRead(BaseModel):
    id: int
    company_id: int
    email: str
    full_name: str
    role_id: Optional[int]
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}


class RoleCreate(BaseModel):
    company_id: int = 1
    name: str
    description: Optional[str] = None
    permissions: list[str] = []


class RoleRead(BaseModel):
    id: int
    name: str
    description: Optional[str]
    status: str
    permissions: list[str] = []

    model_config = {"from_attributes": True}
