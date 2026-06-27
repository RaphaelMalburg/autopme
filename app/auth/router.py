"""Simple password auth for the demo dashboard and API."""
from __future__ import annotations

import secrets

from fastapi import APIRouter, HTTPException, Request, Response
from pydantic import BaseModel

from app.config import settings

auth_router = APIRouter(prefix="/api/auth", tags=["auth"])


def _auth_enabled() -> bool:
    return bool((settings.admin_password or "").strip())


def is_authenticated(request: Request) -> bool:
    if not _auth_enabled():
        return True
    cookie = request.cookies.get(settings.auth_cookie_name, "")
    return secrets.compare_digest(cookie, settings.admin_password or "")


class LoginRequest(BaseModel):
    password: str = ""


@auth_router.get("/me")
async def auth_me(request: Request) -> dict:
    return {"enabled": _auth_enabled(), "authenticated": is_authenticated(request)}


@auth_router.post("/login")
async def auth_login(body: LoginRequest, response: Response) -> dict:
    if not _auth_enabled():
        return {"ok": True, "authenticated": True, "enabled": False}
    if not secrets.compare_digest(body.password or "", settings.admin_password or ""):
        raise HTTPException(status_code=401, detail="senha invalida")
    response.set_cookie(
        key=settings.auth_cookie_name,
        value=settings.admin_password or "",
        httponly=True,
        secure=settings.app_env == "production",
        samesite="lax",
        max_age=60 * 60 * 12,
    )
    return {"ok": True, "authenticated": True, "enabled": True}


@auth_router.post("/logout")
async def auth_logout(response: Response) -> dict:
    response.delete_cookie(settings.auth_cookie_name)
    return {"ok": True}
