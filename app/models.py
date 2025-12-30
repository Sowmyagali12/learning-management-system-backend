# app/models.py
from __future__ import annotations
from datetime import datetime, date
from typing import Optional, List
from enum import Enum as PyEnum

from sqlalchemy import (
    String, Integer, DateTime, Date, ForeignKey, Enum, Boolean, Text, UniqueConstraint, event
)
from sqlalchemy.orm import Mapped, mapped_column, relationship, Session

from app.database import Base


# --- Enums ---

class RoleEnum(str, PyEnum):
    admin = "admin"
    mentor = "mentor"
    student = "student"


class GenderEnum(str, PyEnum):
    male = "male"
    female = "female"
    other = "other"
    prefer_not_to_say = "prefer_not_to_say"


class ModeEnum(str, PyEnum):
    online = "online"
    offline = "offline"
    hybrid = "hybrid"


# --- Core auth user & reset token ---

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    full_name: Mapped[Optional[str]] = mapped_column(String(255))
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[RoleEnum] = mapped_column(Enum(RoleEnum), default=RoleEnum.student, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    phone_number: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)

    student_profile: Mapped[Optional["StudentProfile"]] = relationship(
        back_populates="user", uselist=False, cascade="all, delete-orphan"
    )
    mentor_profile: Mapped[Optional["MentorProfile"]] = relationship(
        back_populates="user", uselist=False, cascade="all, delete-orphan"
    )

    reset_tokens: Mapped[List["PasswordResetToken"]] = relationship(
        "PasswordResetToken", back_populates="user", cascade="all, delete-orphan"
    )


class PasswordResetToken(Base):
    __tablename__ = "password_reset_tokens"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False, index=True
    )
    token: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    used: Mapped[bool] = mapped_column(Boolean, default=False)

    user: Mapped["User"] = relationship("User", back_populates="reset_tokens")


# --- Student profile ---

class StudentProfile(Base):
    __tablename__ = "student_profiles"
    __table_args__ = (
        UniqueConstraint("user_id", name="uq_student_user"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )

    first_name: Mapped[str] = mapped_column(String(100))
    last_name: Mapped[str] = mapped_column(String(100))
    phone_number: Mapped[Optional[str]] = mapped_column(String(20))
    whatsapp_number: Mapped[Optional[str]] = mapped_column(String(20))
    dob: Mapped[Optional[date]] = mapped_column(Date)
    gender: Mapped[Optional[GenderEnum]] = mapped_column(Enum(GenderEnum))
    address: Mapped[Optional[str]] = mapped_column(Text)

    photo_url: Mapped[Optional[str]] = mapped_column(String(512))
    resume_url: Mapped[Optional[str]] = mapped_column(String(512))

    course_interest: Mapped[Optional[str]] = mapped_column(String(255))
    is_referred: Mapped[bool] = mapped_column(Boolean, default=False)
    referral_code: Mapped[Optional[str]] = mapped_column(String(50), index=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    user: Mapped["User"] = relationship("User", back_populates="student_profile")


# --- Technology catalog & mentor link (many-to-many) ---

class Technology(Base):
    __tablename__ = "technologies"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, index=True)

    mentor_links: Mapped[List["MentorTechnology"]] = relationship(
        "MentorTechnology", back_populates="technology", cascade="all, delete-orphan"
    )


class MentorTechnology(Base):
    __tablename__ = "mentor_technologies"
    __table_args__ = (
        UniqueConstraint("mentor_profile_id", "technology_id", name="uq_mentor_tech"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    mentor_profile_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("mentor_profiles.id", ondelete="CASCADE"), nullable=False, index=True
    )
    technology_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("technologies.id", ondelete="CASCADE"), nullable=False, index=True
    )

    mentor_profile: Mapped["MentorProfile"] = relationship("MentorProfile", back_populates="technologies_link")
    technology: Mapped["Technology"] = relationship("Technology", back_populates="mentor_links")


# --- Mentor profile ---

class MentorProfile(Base):
    __tablename__ = "mentor_profiles"
    __table_args__ = (
        UniqueConstraint("user_id", name="uq_mentor_user"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )

    name: Mapped[str] = mapped_column(String(150))
    phone_number: Mapped[Optional[str]] = mapped_column(String(20))
    dob: Mapped[Optional[date]] = mapped_column(Date)
    gender: Mapped[Optional[GenderEnum]] = mapped_column(Enum(GenderEnum))
    address: Mapped[Optional[str]] = mapped_column(Text)

    experience_summary: Mapped[Optional[str]] = mapped_column(Text)
    total_experience_years: Mapped[Optional[int]] = mapped_column(Integer)
    total_experience_months: Mapped[Optional[int]] = mapped_column(Integer)

    resume_url: Mapped[Optional[str]] = mapped_column(String(512))
    linkedin_url: Mapped[Optional[str]] = mapped_column(String(512))
    portfolio_url: Mapped[Optional[str]] = mapped_column(String(512))

    preferred_mode: Mapped[Optional[ModeEnum]] = mapped_column(Enum(ModeEnum))
    availability_hours_per_week: Mapped[Optional[int]] = mapped_column(Integer)

    technologies_link: Mapped[List["MentorTechnology"]] = relationship(
        "MentorTechnology", back_populates="mentor_profile", cascade="all, delete-orphan"
    )

    batches: Mapped[List["Batch"]] = relationship(
        "Batch", back_populates="mentor", cascade="all, delete-orphan"
    )

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    user: Mapped["User"] = relationship("User", back_populates="mentor_profile")


# --- Admin dashboard ---




class AdminDashboard(Base):
    __tablename__ = "admin_dashboard"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    batches_completed_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    students_hired: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    no_of_students: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    no_of_mentors: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    hires: Mapped[List["StudentsHired"]] = relationship(
        "StudentsHired", back_populates="dashboard", cascade="all, delete-orphan"
    )

    def update_counts(self, db: Session):
        """Update dashboard counts"""
        self.students_hired = db.query(StudentsHired).filter(StudentsHired.dashboard_id == self.id).count()
        self.batches_completed_count = db.query(Batch).filter(Batch.status == "Completed").count()
        self.no_of_students = db.query(User).filter(User.role == RoleEnum.student).count()
        self.no_of_mentors = db.query(User).filter(User.role == RoleEnum.mentor).count()


# --- Students hired ---

class StudentsHired(Base):
    __tablename__ = "students_hired"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)

    fullname: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    hired_company: Mapped[str] = mapped_column(String(150), nullable=False)
    hired_date: Mapped[Date] = mapped_column(Date, nullable=False)
    batch_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("batches.id"), nullable=True)
    dashboard_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("admin_dashboard.id"), nullable=True)

    dashboard: Mapped[Optional["AdminDashboard"]] = relationship("AdminDashboard", back_populates="hires")
    batch: Mapped[Optional["Batch"]] = relationship("Batch", back_populates="students_hired")


# --- Batch table ---

class Batch(Base):
    __tablename__ = "batches"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    batch_name: Mapped[str] = mapped_column(String(150), nullable=False)
    no_of_students: Mapped[int] = mapped_column(Integer, nullable=False)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    completion_date: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    mentor_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("mentor_profiles.id", ondelete="SET NULL"), nullable=True, index=True
    )

    mentor: Mapped[Optional["MentorProfile"]] = relationship("MentorProfile", back_populates="batches")
    students_hired: Mapped[List["StudentsHired"]] = relationship(
        "StudentsHired", back_populates="batch", cascade="all, delete-orphan"
    )


# --- Auto-update dashboard counts after hiring ---

@event.listens_for(StudentsHired, "after_insert")
def update_dashboard_counts(mapper, connection, target):
    """Automatically update AdminDashboard counts when a student is hired"""
    db = Session(bind=connection)
    if target.dashboard_id:
        dashboard = db.get(AdminDashboard, target.dashboard_id)
        if dashboard:
            dashboard.update_counts(db)
            db.commit()
