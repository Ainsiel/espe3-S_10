"""
dependencies.py — Dependencias FastAPI: autenticación JWT y RBAC.
Tokens JWT seguros (V031-V032), RBAC por permiso (RNF-01).
"""
from datetime import datetime, timedelta
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from database import get_db
from models.auth import User, RolePermission

# Configuración JWT — en producción usar variables de entorno
SECRET_KEY = "erp-proyecto-cinco-secret-change-in-production-2026"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60
REFRESH_TOKEN_EXPIRE_DAYS = 7

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
bearer_scheme = HTTPBearer()


def verify_password(plain: str, hashed: str) -> bool:
    """Verifica contraseña contra hash bcrypt. V023."""
    return pwd_context.verify(plain, hashed)


def hash_password(password: str) -> str:
    """Genera hash bcrypt. V023: Contraseña nunca en texto plano."""
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Crea JWT de acceso. V031: Token expirado debe rechazarse."""
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire, "type": "access"})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def create_refresh_token(data: dict) -> str:
    """Crea JWT de refresh. V032: Refresh revocado debe rechazarse."""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> dict:
    """Decodifica y valida JWT. Lanza 401 si inválido o expirado."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido o expirado",
            headers={"WWW-Authenticate": "Bearer"},
        )


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    """
    Dependencia: retorna usuario autenticado y activo.
    V019: Usuario debe estar autenticado.
    V020: Usuario debe estar activo.
    V024: Usuario bloqueado no puede iniciar sesión.
    """
    payload = decode_token(credentials.credentials)
    if payload.get("type") != "access":
        raise HTTPException(status_code=401, detail="Token de tipo incorrecto")

    user_id: int = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Token sin subject")

    user = db.query(User).filter(User.id == int(user_id)).first()
    if not user:
        raise HTTPException(status_code=401, detail="Usuario no encontrado")
    if user.status != "active":
        raise HTTPException(status_code=403, detail="Usuario inactivo o bloqueado")

    return user


def require_permission(permission: str):
    """
    Factory de dependencia de permiso RBAC.
    Uso: Depends(require_permission("customers.create"))
    V027-V030: Permiso requerido para operaciones críticas.
    """
    def checker(
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db),
    ) -> User:
        if not current_user.role_id:
            raise HTTPException(status_code=403, detail="Sin rol asignado")

        perm = db.query(RolePermission).filter(
            RolePermission.role_id == current_user.role_id,
            RolePermission.permission_code == permission,
        ).first()

        if not perm:
            raise HTTPException(
                status_code=403,
                detail=f"Permiso requerido: {permission}"
            )
        return current_user

    return checker
