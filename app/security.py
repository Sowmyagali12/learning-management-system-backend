# app/security.py
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

from fastapi import Depends, HTTPException, Security, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt  # PyJWT
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from app.config import (
    JWT_ALG,
    ACCESS_SECRET,
    REFRESH_SECRET,
    ACCESS_MIN,
    REFRESH_DAYS,
)
from app.database import get_db
from app.models import User

# ---- Password hashing ----
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, password_hash: str) -> bool:
    return plain_password == password_hash

# ---- Time helper ----
def _now() -> datetime:
    return datetime.now(timezone.utc)

# ---- Token creation ----
def create_access_token(
    sub: str,
    extra: Optional[Dict[str, Any]] = None,
    minutes: int = ACCESS_MIN,
) -> str:
    payload: Dict[str, Any] = {
        "sub": str(sub),
        "type": "access",
        "iat": int(_now().timestamp()),
        "exp": int((_now() + timedelta(minutes=minutes)).timestamp()),
    }
    if extra:
        payload.update(extra)
    return jwt.encode(payload, ACCESS_SECRET, algorithm=JWT_ALG)

def create_refresh_token(
    sub: str,
    extra: Optional[Dict[str, Any]] = None,
    days: int = REFRESH_DAYS,
) -> str:
    payload: Dict[str, Any] = {
        "sub": str(sub),
        "type": "refresh",
        "iat": int(_now().timestamp()),
        "exp": int((_now() + timedelta(days=days)).timestamp()),
    }
    if extra:
        payload.update(extra)
    return jwt.encode(payload, REFRESH_SECRET, algorithm=JWT_ALG)

# ---- Token decode/validate ----
def decode_access(token: str) -> Dict[str, Any]:
    try:
        payload = jwt.decode(token, ACCESS_SECRET, algorithms=[JWT_ALG])
        if payload.get("type") != "access":
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token type")
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired")
    except jwt.PyJWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

def decode_refresh_token(token: str) -> Dict[str, Any]:
    try:
        payload = jwt.decode(token, REFRESH_SECRET, algorithms=[JWT_ALG])
        if payload.get("type") != "refresh":
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token type")
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token expired")
    except jwt.PyJWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

# ---- Bearer-only security for Swagger (/docs) ----
bearer_scheme = HTTPBearer(auto_error=True)

def get_current_payload(credentials: HTTPAuthorizationCredentials = Security(bearer_scheme)) -> Dict[str, Any]:
    return decode_access(credentials.credentials)

def get_current_user(
    payload: Dict[str, Any] = Depends(get_current_payload),
    db: Session = Depends(get_db),
) -> User:
    user_id = payload.get("sub")
    user = db.get(User, int(user_id)) if user_id is not None else None
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User inactive or not found")
    return user
