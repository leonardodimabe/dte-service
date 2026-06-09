"""Autenticación del portal (login JWT + perfil)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.concurrency import run_blocking
from app.core.security import create_access_token
from app.db.models import User
from app.db.session import get_db
from app.schemas.auth import LoginRequest, MeResponse, TokenResponse
from app.security.auth import get_current_user
from app.services import user_service

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/login", response_model=TokenResponse)
async def login(data: LoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    user = await run_blocking(user_service.authenticate, db, data.email, data.password)
    if user is None:
        raise HTTPException(status_code=401, detail="credenciales inválidas")
    token = create_access_token(user.id, user.role, user.customer_id)
    return TokenResponse(access_token=token, role=user.role, customer_id=user.customer_id)


@router.get("/me", response_model=MeResponse)
async def me(user: User = Depends(get_current_user)) -> User:
    return user
