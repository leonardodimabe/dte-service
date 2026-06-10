"""Autenticación del portal (login JWT + perfil).

Endpoints ``def`` (síncronos): FastAPI los corre en el threadpool, así el
argon2 y la BD no bloquean el event loop.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.security import create_access_token
from app.db.models import User
from app.db.session import get_db
from app.schemas.auth import LoginRequest, MeResponse, TokenResponse
from app.security.auth import get_current_user
from app.security.ratelimit import SlidingWindowLimiter
from app.services import user_service

router = APIRouter(prefix="/auth", tags=["Auth"])

# Cuenta TODO intento de login por IP (éxito incluido): frena fuerza bruta.
_login_limiter = SlidingWindowLimiter(get_settings().login_attempts_per_minute, 60.0)


@router.post("/login", response_model=TokenResponse)
def login(request: Request, data: LoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    ip = request.client.host if request.client else "-"
    if _login_limiter.hit(ip):
        raise HTTPException(status_code=429, detail="demasiados intentos; espera un minuto")
    user = user_service.authenticate(db, data.email, data.password)
    if user is None:
        raise HTTPException(status_code=401, detail="credenciales inválidas")
    token = create_access_token(user.id, user.role, user.customer_id)
    return TokenResponse(access_token=token, role=user.role, customer_id=user.customer_id)


@router.get("/me", response_model=MeResponse)
def me(user: User = Depends(get_current_user)) -> User:
    return user
