from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User, RoleEnum
from app.security import decode_access

# We don’t actually use the OAuth2 form flow here, but this gives us the Authorization: Bearer <access> dependency.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    # Validate & decode access token, then load user
    try:
        payload = decode_access(token)
        email: str = payload.get("sub")
        if not email:
            raise ValueError("No subject in token")
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired access token",
        )
    user = db.query(User).filter(User.email == email).first()
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="Inactive or not found")
    return user

def require_role(required: RoleEnum):
    """Dependency to enforce a single required role."""
    def _checker(user: User = Depends(get_current_user)) -> User:
        if user.role != required:
            raise HTTPException(status_code=403, detail="Forbidden")
        return user
    return _checker

# (Optional) If you want endpoints that allow multiple roles:
def require_any_role(*roles: RoleEnum):
    def _checker(user: User = Depends(get_current_user)) -> User:
        if user.role not in roles:
            raise HTTPException(status_code=403, detail="Forbidden")
        return user
    return _checker

