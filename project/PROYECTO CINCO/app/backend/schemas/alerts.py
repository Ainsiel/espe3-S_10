"""schemas/alerts.py — Schemas de alertas y logs de correo."""
from datetime import datetime
from typing import Optional, List, Any
from pydantic import BaseModel, field_validator


class AlertCreate(BaseModel):
    company_id: int = 1
    name: str
    alert_type: str
    condition: Optional[dict] = None
    recipients: List[str]
    frequency: str = "daily"

    @field_validator("recipients")
    @classmethod
    def has_recipients(cls, v):
        if not v:
            raise ValueError("Alerta requiere al menos un destinatario")
        return v


class AlertUpdate(BaseModel):
    name: Optional[str] = None
    condition: Optional[dict] = None
    recipients: Optional[List[str]] = None
    frequency: Optional[str] = None
    status: Optional[str] = None


class AlertRead(BaseModel):
    id: int
    name: str
    alert_type: str
    recipients: List[str]
    frequency: str
    status: str
    last_sent_at: Optional[datetime]
    model_config = {"from_attributes": True}
