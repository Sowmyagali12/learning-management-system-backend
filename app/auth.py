# from datetime import datetime
# from fastapi import APIRouter, Depends, HTTPException, status
# from sqlalchemy.orm import Session
# from app.database import get_db
# from app.models import User, RoleEnum, PasswordResetToken
# from app.schemas import UserCreate, LoginIn, TokenPair, RefreshIn, ForgotIn, ResetIn, UserOut
# from app.security import hash_password, verify_password, create_access_token, create_refresh_token, decode_refresh
# from app.utils import generate_reset_token

# router = APIRouter(prefix="/auth", tags=["auth"])

# @router.post("/register", response_model=UserOut)
# def register(data: UserCreate, db: Session = Depends(get_db)):
#     if db.query(User).filter(User.email == data.email).first():
#         raise HTTPException(status_code=400, detail="Email already registered")
#     user = User(email=data.email, full_name=data.full_name, hashed_password=hash_password(data.password), role=RoleEnum.student)
#     db.add(user)
#     db.commit()
#     db.refresh(user)
#     return user

# @router.post("/login", response_model=TokenPair)
# def login(form: LoginIn, db: Session = Depends(get_db)):
#     user = db.query(User).filter(User.email == form.email).first()
#     if not user or not verify_password(form.password, user.hashed_password):
#         raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
#     return TokenPair(access_token=create_access_token(user.email), refresh_token=create_refresh_token(user.email))

# @router.post("/refresh", response_model=TokenPair)
# def refresh(data: RefreshIn):
#     try:
#         payload = decode_refresh(data.refresh_token)
#         if payload.get("type") != "refresh":
#             raise ValueError()
#         email = payload["sub"]
#     except Exception:
#         raise HTTPException(status_code=401, detail="Invalid refresh token")
#     return TokenPair(access_token=create_access_token(email), refresh_token=create_refresh_token(email))

# @router.post("/forgot")
# def forgot(data: ForgotIn, db: Session = Depends(get_db)):
#     user = db.query(User).filter(User.email == data.email).first()
#     if user:
#         reset_token = generate_reset_token(db, user)
#         return {"message": "Reset token generated (dev)", "token": reset_token}
#     return {"message": "If the email exists, a reset link has been sent"}

# @router.post("/reset")
# def reset(data: ResetIn, db: Session = Depends(get_db)):
#     prt = db.query(PasswordResetToken).filter(PasswordResetToken.token == data.token).first()
#     if not prt or prt.used or prt.expires_at < datetime.utcnow():
#         raise HTTPException(status_code=400, detail="Invalid or expired token")
#     user = db.get(User, prt.user_id)
#     user.hashed_password = hash_password(data.new_password)
#     prt.used = True
#     db.commit()
#     return {"message": "Password reset successful"}
