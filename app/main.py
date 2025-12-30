# app/main.py
from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi
import os

from app.database import Base, engine, SessionLocal
from app import models  # ensure models are imported so tables are known
from app.models import User, RoleEnum
from app.security import hash_password

# ---- Create tables (no-op if they already exist)
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="LMS API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# ---- Routers
from app.routes.auth import router as auth_router
from app.routes.users import router as users_router
from app.routes.admin import router as admin_router
from app.routes.student import router as student_router

app.include_router(auth_router)
app.include_router(users_router)
app.include_router(admin_router)
app.include_router(student_router)


@app.get("/")
def root():
    return {"status": "ok"}

# ---- Seed a default admin from environment on startup
# Avoid .local/.test/.example/.invalid unless you relaxed EmailStr validation
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")

@app.on_event("startup")
def seed_admin():
    db = SessionLocal()
    try:
        u = db.query(User).filter(User.email == ADMIN_EMAIL).first()
        if not u:
            u = User(
                email=ADMIN_EMAIL,
                full_name="Admin",
                hashed_password=ADMIN_PASSWORD,
                role=RoleEnum.admin,
                is_active=True,
            )
            db.add(u)
            db.commit()
            print(f"[startup] Seeded admin user: {ADMIN_EMAIL}")
        else:
            changed = False
            if u.role != RoleEnum.admin:
                u.role = RoleEnum.admin
                changed = True
            if not u.is_active:
                u.is_active = True
                changed = True
            if changed:
                db.commit()
                print(f"[startup] Ensured {ADMIN_EMAIL} is admin & active")
    finally:
        db.close()

# ---- Keep schemas, add Bearer-only security in OpenAPI
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=getattr(app, "description", None),
        routes=app.routes,
    )

    comps = openapi_schema.setdefault("components", {})
    comps.setdefault("schemas", {})  # keep your Pydantic models intact
    security_schemes = comps.setdefault("securitySchemes", {})

    # Remove leftover OAuth2 entries (optional)
    security_schemes.pop("OAuth2PasswordBearer", None)
    security_schemes.pop("OAuth2", None)

    # Add HTTP Bearer
    security_schemes["HTTPBearer"] = {"type": "http", "scheme": "bearer", "bearerFormat": "JWT"}

    # Make Bearer the default requirement for all endpoints
    openapi_schema["security"] = [{"HTTPBearer": []}]

    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi
