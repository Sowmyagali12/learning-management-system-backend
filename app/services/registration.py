# app/services/registration.py
from __future__ import annotations
from typing import List, Optional
from sqlalchemy.orm import Session
from passlib.context import CryptContext

from app.models import (
    User, RoleEnum,
    StudentProfile, MentorProfile,
    Technology, MentorTechnology
)
from app.schemas import StudentRegisterIn, MentorRegisterIn

pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")

def _get_or_create_technologies(db: Session, names: List[str]) -> List[Technology]:
    out: List[Technology] = []
    for raw in names:
        name = (raw or "").strip()
        if not name:
            continue
        existing = db.query(Technology).filter(Technology.name.ilike(name)).one_or_none()
        if not existing:
            existing = Technology(name=name)
            db.add(existing)
            db.flush()
        out.append(existing)
    return out

def create_student(
    db: Session,
    data: StudentRegisterIn,
    *,
    photo_url: str | None,
    document_url: str | None
) -> User:
    full_name = f"{data.first_name} {data.last_name}".strip()
    user = User(
        email=data.email.strip().lower(),
        full_name=full_name,
        phone_number=data.phone_number,
        hashed_password=data.password,
        role=RoleEnum.student,
        is_active=True,
    )
    try:
        db.add(user)
        db.flush()  # get user.id

        profile = StudentProfile(
            user_id=user.id,
            first_name=data.first_name,
            last_name=data.last_name,
            gender=data.gender,
            course_interest=data.course_interest,
            referral_code=data.referral_code,
            is_referred=data.is_referred,
            address=data.address,
            dob=data.dob,  # already a date
            whatsapp_number=data.whatsapp_number,
            photo_url=photo_url,
            resume_url=document_url,
        )
        db.add(profile)
        db.commit()
        db.refresh(user)
        return user
    except Exception:
        db.rollback()
        raise

def create_mentor(db: Session, payload: MentorRegisterIn,
                  resume_url: Optional[str] = None) -> User:
    user = User(
        email=str(payload.email).lower().strip(),
        full_name=payload.name,
        hashed_password=payload.password,
        role=RoleEnum.mentor,
        phone_number=payload.phone_number,
    )
    db.add(user)
    db.flush()

    mp = MentorProfile(
        user_id=user.id,
        name=payload.name,
        phone_number=payload.phone_number,
        dob=payload.dob,
        gender=payload.gender,
        address=payload.address,
        total_experience_years=payload.total_experience_years,
        total_experience_months=payload.total_experience_months,
        experience_summary=payload.experience_summary,
        preferred_mode=payload.preferred_mode,
        availability_hours_per_week=payload.availability_hours_per_week,
        resume_url=resume_url,
        linkedin_url=payload.linkedin_url,
        portfolio_url=payload.portfolio_url,
    )
    db.add(mp)
    db.flush()

    techs = _get_or_create_technologies(db, payload.technologies)
    for t in techs:
        db.add(MentorTechnology(mentor_profile_id=mp.id, technology_id=t.id))

    db.commit()
    db.refresh(user)
    return user
