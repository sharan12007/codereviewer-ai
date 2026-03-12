import logging
import os
import secrets
from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException, Request, Depends
from fastapi.responses import RedirectResponse
from jose import jwt
import httpx
from sqlmodel import Session, select
from config import settings
from database import get_session
from models import User
from cryptography.fernet import Fernet

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth")

# In-memory state store with TTL
_state_store: dict[str, datetime] = {}
STATE_TTL_MINUTES = 5


def _clean_states():
    now = datetime.utcnow()
    expired = [k for k, v in _state_store.items() if (now - v).seconds > STATE_TTL_MINUTES * 60]
    for k in expired:
        del _state_store[k]


def create_jwt(github_id: int, login: str) -> str:
    payload = {
        "sub": str(github_id),
        "login": login,
        "exp": datetime.utcnow() + timedelta(days=7),
        "iat": datetime.utcnow(),
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm="HS256")


def decrypt_token(enc: str) -> str:
    f = Fernet(settings.ENCRYPTION_KEY.encode())
    return f.decrypt(enc.encode()).decode()


def encrypt_token(token: str) -> str:
    f = Fernet(settings.ENCRYPTION_KEY.encode())
    return f.encrypt(token.encode()).decode()


@router.post("/github")
async def auth_github(redirect_uri: str = "vscode://ai-reviewer/callback"):
    _clean_states()
    state = secrets.token_urlsafe(32)
    _state_store[state] = datetime.utcnow()

    github_oauth_url = (
        f"https://github.com/login/oauth/authorize"
        f"?client_id={settings.GITHUB_CLIENT_ID}"
        f"&redirect_uri={redirect_uri}"
        f"&scope=read:user"
        f"&state={state}"
    )
    return {"url": github_oauth_url, "state": state}


@router.get("/callback")
async def auth_callback(
    code: str,
    state: str,
    session: Session = Depends(get_session)
):
    _clean_states()
    if state not in _state_store:
        raise HTTPException(status_code=400, detail="Invalid or expired state")
    del _state_store[state]

    # Exchange code for token
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            "https://github.com/login/oauth/access_token",
            json={
                "client_id": settings.GITHUB_CLIENT_ID,
                "client_secret": settings.GITHUB_CLIENT_SECRET,
                "code": code,
            },
            headers={"Accept": "application/json"},
        )
        token_data = resp.json()

    access_token = token_data.get("access_token")
    if not access_token:
        raise HTTPException(status_code=400, detail="Failed to get access token")

    # Fetch GitHub user
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            "https://api.github.com/user",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        user_data = resp.json()

    github_id = user_data.get("id")
    github_login = user_data.get("login")

    # Upsert user
    user = session.exec(select(User).where(User.github_id == github_id)).first()
    encrypted = encrypt_token(access_token)

    if user:
        user.github_login = github_login
        user.email = user_data.get("email")
        user.access_token_enc = encrypted
    else:
        user = User(
            github_id=github_id,
            github_login=github_login,
            email=user_data.get("email"),
            access_token_enc=encrypted,
        )

    session.add(user)
    session.commit()

    jwt_token = create_jwt(github_id, github_login)
    return RedirectResponse(url=f"vscode://ai-reviewer/callback?token={jwt_token}")


@router.get("/me")
async def auth_me(request: Request, session: Session = Depends(get_session)):
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing token")

    token = auth_header.split(" ")[1]
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=["HS256"])
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")

    github_id = int(payload.get("sub"))
    user = session.exec(select(User).where(User.github_id == github_id)).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return {
        "github_id": user.github_id,
        "github_login": user.github_login,
        "email": user.email,
    }

