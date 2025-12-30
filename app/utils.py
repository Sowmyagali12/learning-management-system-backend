import secrets
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.models import PasswordResetToken, User

def generate_reset_token(db: Session, user: User) -> str:
    token = secrets.token_urlsafe(48)
    expires = datetime.utcnow() + timedelta(minutes=30)
    db.add(PasswordResetToken(user_id=user.id, token=token, expires_at=expires))
    db.commit()
    return token
