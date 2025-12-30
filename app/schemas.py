# app/schemas.py
from __future__ import annotations
from typing import Optional, List, Annotated
from datetime import date

from fastapi import Form
from pydantic import BaseModel, Field, ConfigDict, field_validator, EmailStr
from pydantic import FieldValidationInfo  # pydantic v2

# Pull enums from your models to avoid duplication
from app.models import RoleEnum, GenderEnum, ModeEnum

# ------------------------
# Helpers
# ------------------------
def _allow_local_email(v: str) -> str:
    v = (v or "").strip()
    if "@" not in v or v.startswith("@") or v.endswith("@"):
        raise ValueError("Invalid email format")
    return v.lower()


# ------------------------
# Token schemas
# ------------------------
class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


# ------------------------
# User schemas (core)
# ------------------------
class UserBase(BaseModel):
    email: str
    full_name: Optional[str] = Field(default=None, alias="fullName")
    phone_number: Optional[str] = Field(default=None, alias="phoneNumber")
    whatsapp_number: Optional[str] = Field(default=None, alias="whatsappNumber")
    dob: Optional[str] = Field(default=None, alias="DOB")
    gender: Optional[str] = Field(default=None, alias="gender")
    address: Optional[str] = Field(default=None, alias="address")
    password: Optional[str] = Field(default=None, alias="password")
    confirm_password: Optional[str] = Field(default=None, alias="confirmPassword")
    upload_photo: Optional[str] = Field(default=None, alias="uploadPhoto")
    upload_resume: Optional[str] = Field(default=None, alias="uploadResume")
    course_interest: Optional[str] = Field(default=None, alias="courseInterest")
    is_referred: Optional[bool] = Field(default=False, alias="isReferred")

    model_config = ConfigDict(populate_by_name=True)

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        return _allow_local_email(v)


class UserCreate(UserBase):
    password: str


class UserOut(BaseModel):
    id: int
    email: str
    full_name: Optional[str] = None
    phone_number: Optional[str] = None
    role: RoleEnum | str
    is_active: bool

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


# ------------------------
# Auth input schemas
# ------------------------
class LoginIn(BaseModel):
    email: str
    password: str

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        return _allow_local_email(v)


class RefreshIn(BaseModel):
    refresh_token: str


class ForgotIn(BaseModel):
    email: str

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        return _allow_local_email(v)


class ResetIn(BaseModel):
    token: str
    new_password: str


# ------------------------
# Admin schemas (create mentor via admin)
# ------------------------
class MentorCreate(BaseModel):
    email: str
    full_name: Optional[str] = Field(default=None, alias="fullName")
    phone_number: Optional[str] = Field(default=None, alias="phoneNumber")
    password: str

    model_config = ConfigDict(populate_by_name=True)

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        return _allow_local_email(v)

# ======================================================================
# Role-specific registration & profile schemas
# ======================================================================

# ---------- Student ----------
class StudentRegisterIn(BaseModel):
    # exact field names
    first_name: str = Field(alias="firstName")
    last_name: str = Field(alias="lastName")
    gender: str
    course_interest: Optional[str] = Field(default=None, alias="courseInterest")
    referral_code: Optional[str] = Field(default=None, alias="referralCode")
    address: Optional[str] = None
    dob: date
    phone_number: str = Field(alias="phoneNumber")
    whatsapp_number: Optional[str] = Field(default=None, alias="whatsappNumber")
    email: EmailStr
    password: str
    confirm_password: str
    is_referred: bool = Field(alias="isReferred")

    @field_validator("confirm_password")
    @classmethod
    def _passwords_match(cls, v: str, info: FieldValidationInfo) -> str:
        password = info.data.get("password")
        if password and v != password:
            raise ValueError("Passwords do not match")
        return v

    @field_validator("gender")
    @classmethod
    def _gender_ok(cls, v: str) -> str:
        allowed = {"male", "female", "other"}
        if v.lower() not in allowed:
            raise ValueError(f"gender must be one of {allowed}")
        return v.lower()

    # Accept as multipart/form-data
    @classmethod
    def as_form(
        cls,
        # REQUIRED first
        firstName: Annotated[str, Form(...)],
        lastName: Annotated[str, Form(...)],
        gender: Annotated[str, Form(...)],
        dob: Annotated[str, Form(...)],            # YYYY-MM-DD
        phoneNumber: Annotated[str, Form(...)],
        email: Annotated[str, Form(...)],
        password: Annotated[str, Form(...)],
        confirm_password: Annotated[str, Form(...)],
        # OPTIONAL after
        isReferred: Annotated[bool, Form()] = False,
        courseInterest: Annotated[Optional[str], Form()] = None,
        referralCode: Annotated[Optional[str], Form()] = None,
        address: Annotated[Optional[str], Form()] = None,
        whatsappNumber: Annotated[Optional[str], Form()] = None,
    ):
        return cls(
            firstName=firstName,
            lastName=lastName,
            gender=gender,
            courseInterest=courseInterest,
            referralCode=referralCode,
            address=address,
            dob=dob,
            phoneNumber=phoneNumber,
            whatsappNumber=whatsappNumber,
            email=email,
            password=password,
            confirm_password=confirm_password,
            isReferred=isReferred,
        )

class StudentOut(BaseModel):
    user: UserOut
    first_name: str = Field(alias="firstName")
    last_name: str = Field(alias="lastName")
    phone_number: Optional[str] = Field(default=None, alias="phoneNumber")
    whatsapp_number: Optional[str] = Field(default=None, alias="whatsappNumber")
    dob: Optional[date] = None
    gender: Optional[GenderEnum] = None
    address: Optional[str] = None
    course_interest: Optional[str] = Field(default=None, alias="courseInterest")
    is_referred: bool = Field(alias="isReferred")
    referral_code: Optional[str] = Field(default=None, alias="referralCode")
    photo_url: Optional[str] = Field(default=None, alias="photoUrl")
    resume_url: Optional[str] = Field(default=None, alias="resumeUrl")

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

# ---------- Mentor ----------
class MentorRegisterIn(BaseModel):
    # auth
    email: EmailStr
    password: str = Field(min_length=8)
    confirm_password: str = Field(min_length=8)

    # profile
    name: str
    phone_number: Optional[str] = Field(default=None, alias="phoneNumber")
    dob: Optional[date] = None
    gender: Optional[GenderEnum] = None
    address: Optional[str] = None

    # experience
    total_experience_years: Optional[int] = Field(default=None, ge=0, le=60, alias="totalExperienceYears")
    total_experience_months: Optional[int] = Field(default=None, ge=0, le=11, alias="totalExperienceMonths")
    experience_summary: Optional[str] = Field(default=None, alias="experienceSummary")

    # preferences
    preferred_mode: Optional[ModeEnum] = Field(default=None, alias="preferredMode")
    availability_hours_per_week: Optional[int] = Field(default=None, ge=0, le=80, alias="availabilityHoursPerWeek")

    # techs by name
    technologies: List[str] = Field(default_factory=list)

    # uploads & links
    linkedin_url: Optional[str] = Field(default=None, alias="linkedinUrl")
    portfolio_url: Optional[str] = Field(default=None, alias="portfolioUrl")

    model_config = ConfigDict(populate_by_name=True)

    @field_validator("email")
    @classmethod
    def validate_email_local(cls, v: EmailStr) -> str:
        return _allow_local_email(str(v))

    @field_validator("confirm_password")
    @classmethod
    def passwords_match(cls, v: str, info: FieldValidationInfo) -> str:
        pw = info.data.get("password")
        if pw != v:
            raise ValueError("Passwords do not match")
        return v
    @classmethod
    def as_form(
        cls,
        # REQUIRED first (no defaults)
        email: Annotated[str, Form(...)],
        password: Annotated[str, Form(...)],
        confirm_password: Annotated[str, Form(...)],
        name: Annotated[str, Form(...)],

        # OPTIONAL after (defaults set with '='; not inside Form)
        phoneNumber: Annotated[Optional[str], Form()] = None,
        dob: Annotated[Optional[str], Form()] = None,             # "YYYY-MM-DD" (Pydantic parses to date)
        gender: Annotated[Optional[str], Form()] = None,          # "male"/"female"/"other" (to GenderEnum)
        address: Annotated[Optional[str], Form()] = None,

        totalExperienceYears: Annotated[Optional[int], Form()] = None,
        totalExperienceMonths: Annotated[Optional[int], Form()] = None,
        experienceSummary: Annotated[Optional[str], Form()] = None,

        preferredMode: Annotated[Optional[str], Form()] = None,   # to ModeEnum
        availabilityHoursPerWeek: Annotated[Optional[int], Form()] = None,

        # For lists in multipart/form-data, repeat the key: technologies=React&technologies=FastAPI ...
        technologies: Annotated[Optional[List[str]], Form()] = None,

        linkedinUrl: Annotated[Optional[str], Form()] = None,
        portfolioUrl: Annotated[Optional[str], Form()] = None,
    ):
        return cls(
            email=email,
            password=password,
            confirm_password=confirm_password,
            name=name,
            phone_number=phoneNumber,
            dob=dob,  # Pydantic will parse "YYYY-MM-DD" to date
            gender=gender,  # Pydantic will coerce to GenderEnum if provided
            address=address,
            total_experience_years=totalExperienceYears,
            total_experience_months=totalExperienceMonths,
            experience_summary=experienceSummary,
            preferred_mode=preferredMode,  # coerces to ModeEnum
            availability_hours_per_week=availabilityHoursPerWeek,
            technologies=technologies or [],  # avoid mutable default
            linkedin_url=linkedinUrl,
            portfolio_url=portfolioUrl,
        )

class MentorOut(BaseModel):
    user: UserOut
    name: str
    phone_number: Optional[str] = Field(default=None, alias="phoneNumber")
    dob: Optional[date] = None
    gender: Optional[GenderEnum] = None
    address: Optional[str] = None
    # experience
    total_experience_years: Optional[int] = Field(default=None, alias="totalExperienceYears")
    total_experience_months: Optional[int] = Field(default=None, alias="totalExperienceMonths")
    experience_summary: Optional[str] = Field(default=None, alias="experienceSummary")
    # preferences
    preferred_mode: Optional[ModeEnum] = Field(default=None, alias="preferredMode")
    availability_hours_per_week: Optional[int] = Field(default=None, alias="availabilityHoursPerWeek")
    # technologies
    technologies: List[str] = Field(default_factory=list)
    # uploads & links
    resume_url: Optional[str] = Field(default=None, alias="resumeUrl")
    linkedin_url: Optional[str] = Field(default=None, alias="linkedinUrl")
    portfolio_url: Optional[str] = Field(default=None, alias="portfolioUrl")

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

class TechnologyOut(BaseModel):
    id: int
    name: str
    model_config = ConfigDict(from_attributes=True)

# --- Combined "me" payload ---
class MeOut(BaseModel):
    user: UserOut
    student_profile: Optional[StudentOut] = Field(default=None, alias="studentProfile")
    mentor_profile: Optional[MentorOut] = Field(default=None, alias="mentorProfile")

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


# ------------------------
# Admin dashboard schemas
# ------------------------


class AdminDashboardOut(BaseModel):
    id: int
    batches_completed_count: int
    students_hired: int
    no_of_students: int
    no_of_mentors: int

    model_config = ConfigDict(from_attributes=True)

# class AdminDashboardOut(BaseModel):
#     id: int

#     batches_completed_count: int = Field(alias="batchesCompleted")
#     students_hired: int = Field(alias="studentsHired")
#     no_of_students: int = Field(alias="noOfStudents")
#     no_of_mentors: int = Field(alias="noOfMentors")

#     model_config = ConfigDict(from_attributes=True, populate_by_name=True)









# --- Rebuild (helps with forward-ref edges in Pydantic v2) ---
try:
    StudentRegisterIn.model_rebuild()
    MentorRegisterIn.model_rebuild()
    StudentOut.model_rebuild()
    MentorOut.model_rebuild()
    MeOut.model_rebuild()
except Exception:
    pass
