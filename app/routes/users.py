# app/routes/users.py
from __future__ import annotations
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session, selectinload
from sqlalchemy import func

from app.database import get_db
from app.deps import get_current_user
from app.models import (
    User,
    StudentProfile,
    MentorProfile,
    MentorTechnology,
    Technology,
    RoleEnum,
)
from app.schemas import (
    UserOut,
    StudentOut,
    MentorOut,
    MeOut,
)

router = APIRouter(prefix="/users", tags=["users"])

# ---------------------------
# Helpers
# ---------------------------

def _ensure_admin(user: User):
    if str(user.role) != str(RoleEnum.admin):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")

def _flatten_mentor(mentor: MentorProfile) -> MentorOut:
    # collect technology names
    tech_names = [
        link.technology.name
        for link in (mentor.technologies_link or [])
        if link.technology is not None
    ]
    # validate + inject technologies list
    base = MentorOut.model_validate(mentor)
    data = base.model_dump(by_alias=True)
    data["technologies"] = tech_names
    return MentorOut(**data)

# ---------------------------
# /users/me - combined
# ---------------------------

@router.get("/me", response_model=MeOut)
def get_my_profile(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    user: User = (
        db.query(User)
        .options(
            selectinload(User.student_profile),
            selectinload(User.mentor_profile)
                .selectinload(MentorProfile.technologies_link)
                .selectinload(MentorTechnology.technology)
        )
        .filter(User.id == current_user.id)
        .first()
    )
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    student_payload = StudentOut.model_validate(user.student_profile) if user.student_profile else None
    mentor_payload = _flatten_mentor(user.mentor_profile) if user.mentor_profile else None

    return MeOut(
        user=UserOut.model_validate(user),
        studentProfile=student_payload,
        mentorProfile=mentor_payload,
    )

# ---------------------------
# /users/{user_id} - combined (admin only)
# ---------------------------

@router.get("/{user_id}", response_model=MeOut)
def get_user_by_id(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _ensure_admin(current_user)

    user: User = (
        db.query(User)
        .options(
            selectinload(User.student_profile),
            selectinload(User.mentor_profile)
                .selectinload(MentorProfile.technologies_link)
                .selectinload(MentorTechnology.technology)
        )
        .filter(User.id == user_id)
        .first()
    )
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    student_payload = StudentOut.model_validate(user.student_profile) if user.student_profile else None
    mentor_payload = _flatten_mentor(user.mentor_profile) if user.mentor_profile else None

    return MeOut(
        user=UserOut.model_validate(user),
        studentProfile=student_payload,
        mentorProfile=mentor_payload,
    )

# ---------------------------
# /students - list (paginated)
# ---------------------------

@router.get("/students", response_model=List[StudentOut])
def list_students(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None, description="Search by name, email, phone"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # (Optional) allow all authenticated users; tighten if needed
    q = (
        db.query(StudentProfile)
        .join(User, StudentProfile.user_id == User.id)
        .options(selectinload(StudentProfile.user))
    )

    if search:
        like = f"%{search.strip()}%"
        q = q.filter(
            (StudentProfile.first_name.ilike(like)) |
            (StudentProfile.last_name.ilike(like))  |
            (User.email.ilike(like))                |
            (StudentProfile.phone_number.ilike(like))
        )

    items = q.offset(skip).limit(limit).all()
    return [StudentOut.model_validate(sp) for sp in items]

# ---------------------------
# /students/{id} - single
# ---------------------------

@router.get("/students/{student_id}", response_model=StudentOut)
def get_student(
    student_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    sp: Optional[StudentProfile] = (
        db.query(StudentProfile)
        .options(selectinload(StudentProfile.user))
        .filter(StudentProfile.id == student_id)
        .first()
    )
    if not sp:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student not found")
    return StudentOut.model_validate(sp)

# ---------------------------
# /mentors - list (paginated + filters)
# ---------------------------

@router.get("/mentors", response_model=List[MentorOut])
def list_mentors(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    technology: Optional[str] = Query(None, description="Filter by technology name (case-insensitive)"),
    min_years: Optional[int] = Query(None, ge=0, description="Minimum total experience (years)"),
    search: Optional[str] = Query(None, description="Search by name, email, phone"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    q = (
        db.query(MentorProfile)
        .join(User, MentorProfile.user_id == User.id)
        .options(
            selectinload(MentorProfile.user),
            selectinload(MentorProfile.technologies_link)
                .selectinload(MentorTechnology.technology)
        )
    )

    if search:
        like = f"%{search.strip()}%"
        q = q.filter(
            (MentorProfile.name.ilike(like)) |
            (User.email.ilike(like))         |
            (MentorProfile.phone_number.ilike(like))
        )

    if technology:
        # case-insensitive tech name filter
        q = q.join(MentorTechnology, MentorTechnology.mentor_profile_id == MentorProfile.id) \
             .join(Technology, Technology.id == MentorTechnology.technology_id) \
             .filter(Technology.name.ilike(technology.strip()))

    if min_years is not None:
        q = q.filter((MentorProfile.total_experience_years >= min_years))

    items = q.offset(skip).limit(limit).all()
    return [_flatten_mentor(mp) for mp in items]

# ---------------------------
# /mentors/{id} - single
# ---------------------------

@router.get("/mentors/{mentor_id}", response_model=MentorOut)
def get_mentor(
    mentor_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    mp: Optional[MentorProfile] = (
        db.query(MentorProfile)
        .options(
            selectinload(MentorProfile.user),
            selectinload(MentorProfile.technologies_link)
                .selectinload(MentorTechnology.technology)
        )
        .filter(MentorProfile.id == mentor_id)
        .first()
    )
    if not mp:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Mentor not found")
    return _flatten_mentor(mp)
