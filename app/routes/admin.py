# app/routes/admin.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.deps import require_role
from app.models import RoleEnum, User, StudentsHired, AdminDashboard
from app.database import get_db
from app.schemas import MentorCreate, UserOut, AdminDashboardOut
from app.security import hash_password

router = APIRouter(prefix="/admin", tags=["admin"])


# ------------------------
# Create Mentor (Admin Only)
# ------------------------
@router.post(
    "/create-mentor",
    response_model=UserOut,
    dependencies=[Depends(require_role(RoleEnum.admin))]
)
def create_mentor(data: MentorCreate, db: Session = Depends(get_db)):
    """Admin can create mentor accounts."""
    # Check for duplicate email
    if db.query(User).filter(User.email == data.email).first():
        raise HTTPException(status_code=400, detail="Email already exists")

    # Create mentor user
    mentor = User(
        email=data.email,
        full_name=data.full_name,
        phone_number=data.phoneNumber,
        hashed_password=hash_password(data.password),
        role=RoleEnum.mentor,
    )
    db.add(mentor)
    db.commit()
    db.refresh(mentor)
    return mentor


# ------------------------
# Admin Dashboard Endpoint
# ------------------------
@router.get(
    "/dashboard",
    response_model=AdminDashboardOut,
    dependencies=[Depends(require_role(RoleEnum.admin))]
)
def get_admin_dashboard(db: Session = Depends(get_db)):
    dashboard = db.query(AdminDashboard).first()

    if not dashboard:
        dashboard = AdminDashboard()
        db.add(dashboard)
        db.commit()
        db.refresh(dashboard)

    return dashboard

