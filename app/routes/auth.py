# app/routes/auth.py
from __future__ import annotations
from datetime import datetime, timedelta, timezone
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User, RoleEnum, PasswordResetToken
from app.schemas import (
    LoginIn,
    TokenPair,
    UserOut,
    RefreshIn,
    ForgotIn,
    ResetIn,
    StudentRegisterIn,
    MentorRegisterIn,
)
from app.security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_refresh_token,
)
from app.services.registration import create_student, create_mentor
import json

router = APIRouter(prefix="/auth", tags=["auth"])

# ---------------------------
# Helpers
# ---------------------------
def _normalize_email(email: Optional[str]) -> str:
    return (email or "").strip().lower()

def _ensure_unique_email(db: Session, email: str):
    if db.query(User).filter(User.email == email).first():
        raise HTTPException(status_code=400, detail="Email already registered")

async def _save_upload(file: Optional[UploadFile], subdir: str) -> Optional[str]:
    if not file:
        return None
    import os, uuid, pathlib
    upload_root = "uploads"
    os.makedirs(f"{upload_root}/{subdir}", exist_ok=True)
    ext = pathlib.Path(file.filename or "").suffix or ""
    name = f"{uuid.uuid4().hex}{ext}"
    path = f"{upload_root}/{subdir}/{name}"
    with open(path, "wb") as f:
        f.write(await file.read())
    return f"/{path}"

# ---------------------------
# Student register (JSON + files)
# ---------------------------
@router.post("/register/student", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def register_student(
    data: str = Form(...),
    db: Session = Depends(get_db),
    photo: UploadFile | None = File(None),
    document: UploadFile | None = File(None),
):
    payload_dict = json.loads(data)
    payload = StudentRegisterIn(**payload_dict)

    email = _normalize_email(str(payload.email))
    _ensure_unique_email(db, email)

    photo_url = await _save_upload(photo, "student/photos") if photo else None
    document_url = await _save_upload(document, "student/docs") if document else None

    user = create_student(db, payload, photo_url=photo_url, document_url=document_url)
    return user

# ---------------------------
# Mentor register (JSON + file)
# ---------------------------
@router.post("/register/mentor", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def register_mentor(
    data: str = Form(...),
    db: Session = Depends(get_db),
    resume: UploadFile | None = File(None),
):
    payload_dict = json.loads(data)
    payload = MentorRegisterIn(**payload_dict)

    email = _normalize_email(str(payload.email))
    _ensure_unique_email(db, email)

    resume_url = await _save_upload(resume, "mentor/resumes") if resume else None
    user = create_mentor(db, payload, resume_url=resume_url)
    return user

# ---------------------------
# Login / Refresh (JSON only)
# ---------------------------
@router.post("/login", response_model=TokenPair)
def login(form: LoginIn, db: Session = Depends(get_db)):
    email = _normalize_email(form.email)
    user = db.query(User).filter(User.email == email).first()
    if not user or not verify_password(form.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    access_token = create_access_token(sub=str(user.id), extra={"role": str(user.role)})
    refresh_token = create_refresh_token(sub=str(user.id))
    return TokenPair(access_token=access_token, refresh_token=refresh_token)

@router.post("/refresh", response_model=TokenPair)
def refresh(data: RefreshIn):
    try:
        payload = decode_refresh_token(data.refresh_token)
        if payload.get("type") != "refresh":
            raise ValueError("Not a refresh token")
        user_id = payload["sub"]
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

    return TokenPair(
        access_token=create_access_token(sub=user_id),
        refresh_token=create_refresh_token(sub=user_id),
    )

# ---------------------------
# Forgot / Reset password (JSON only)
# ---------------------------
@router.post("/forgot")
def forgot(data: ForgotIn, db: Session = Depends(get_db)):
    email = _normalize_email(data.email)
    user = db.query(User).filter(User.email == email).first()
    if user:
        reset_token = generate_reset_token(db, user)
        return {"message": "Reset token generated (dev)", "token": reset_token}
    return {"message": "If the email exists, a reset link has been sent"}

@router.post("/reset")
def reset(data: ResetIn, db: Session = Depends(get_db)):
    prt = db.query(PasswordResetToken).filter(PasswordResetToken.token == data.token).first()
    now = datetime.now(timezone.utc)

    if not prt or prt.used or prt.expires_at <= now:
        raise HTTPException(status_code=400, detail="Invalid or expired token")

    user = db.get(User, prt.user_id)
    if not user:
        raise HTTPException(status_code=400, detail="Invalid token")

    user.hashed_password = hash_password(data.new_password)
    prt.used = True
    db.commit()
    return {"message": "Password reset successful"}

# ---------------------------
# Internal helper
# ---------------------------
def generate_reset_token(db: Session, user: User, lifetime_minutes: int = 30) -> str:
    import secrets
    raw = secrets.token_urlsafe(32)
    record = PasswordResetToken(
        user_id=user.id,
        token=raw,
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=lifetime_minutes),
        used=False,
    )
    db.add(record)
    db.commit()
    return raw