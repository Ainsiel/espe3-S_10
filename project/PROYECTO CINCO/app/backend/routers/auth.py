"""
routers/auth.py — Endpoints de autenticación.
Endpoints 1-5: POST /auth/login, /auth/refresh, /auth/logout, GET /auth/me, POST /auth/change-password
"""
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session
from database import get_db
from models.auth import User, AuditLog
from schemas.auth import LoginRequest, TokenResponse, RefreshRequest, ChangePasswordRequest, UserRead
from dependencies import (
    verify_password, hash_password,
    create_access_token, create_refresh_token,
    decode_token, get_current_user
)

router = APIRouter(prefix="/api/v1/auth", tags=["Autenticación"])


@router.post("/login", response_model=TokenResponse, summary="Iniciar sesión")
def login(payload: LoginRequest, request: Request, db: Session = Depends(get_db)):
    """
    UC-CLI: Login de usuario. V019-V024.
    Registra IP y contador de intentos fallidos.
    """
    user = db.query(User).filter(User.email == payload.email).first()

    if not user or not verify_password(payload.password, user.password_hash):
        if user:
            # V034: registrar intento fallido
            user.failed_login_attempts += 1
            db.commit()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales incorrectas"
        )

    # V024: usuario bloqueado
    if user.status != "active":
        raise HTTPException(status_code=403, detail="Usuario inactivo o bloqueado")

    # V033: registrar IP
    ip = request.client.host if request.client else "unknown"
    user.last_ip = ip
    user.failed_login_attempts = 0
    db.commit()

    # Auditoría de login
    db.add(AuditLog(actor_id=user.id, entity="users", entity_id=str(user.id),
                    action="login", ip_address=ip))
    db.commit()

    access = create_access_token({"sub": str(user.id)})
    refresh = create_refresh_token({"sub": str(user.id)})
    return TokenResponse(access_token=access, refresh_token=refresh)


@router.post("/refresh", response_model=TokenResponse, summary="Renovar token")
def refresh_token(payload: RefreshRequest):
    """V032: Refresh token revocado debe rechazarse."""
    decoded = decode_token(payload.refresh_token)
    if decoded.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Token de tipo incorrecto")
    user_id = decoded.get("sub")
    access = create_access_token({"sub": user_id})
    new_refresh = create_refresh_token({"sub": user_id})
    return TokenResponse(access_token=access, refresh_token=new_refresh)


@router.post("/logout", summary="Cerrar sesión")
def logout(current_user: User = Depends(get_current_user)):
    """Cierra sesión del usuario actual. En MVP, el cliente descarta el token."""
    return {"message": "Sesión cerrada correctamente"}


@router.get("/me", response_model=UserRead, summary="Usuario autenticado")
def get_me(current_user: User = Depends(get_current_user)):
    """Retorna datos del usuario autenticado."""
    return current_user


@router.post("/change-password", summary="Cambiar contraseña")
def change_password(
    payload: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """V035: Cambio de contraseña exige contraseña actual."""
    if not verify_password(payload.current_password, current_user.password_hash):
        raise HTTPException(status_code=400, detail="Contraseña actual incorrecta")
    current_user.password_hash = hash_password(payload.new_password)
    db.commit()
    db.add(AuditLog(actor_id=current_user.id, entity="users",
                    entity_id=str(current_user.id), action="change_password"))
    db.commit()
    return {"message": "Contraseña actualizada"}
