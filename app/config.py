# app/config.py
import os
from dotenv import load_dotenv

load_dotenv()  # loads from .env

class Settings:
    DATABASE_URL = os.getenv("DATABASE_URL")
    JWT_SECRET = os.getenv("JWT_SECRET")
    JWT_REFRESH_SECRET = os.getenv("JWT_REFRESH_SECRET")
    ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30))
    REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", 7))
    ADMIN_EMAIL = os.getenv("ADMIN_EMAIL")
    ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")

settings = Settings()

# ---- add these exports so imports like `from app.config import JWT_ALG, ACCESS_SECRET, REFRESH_SECRET` work
JWT_ALG = os.getenv("JWT_ALG", "HS256")
ACCESS_SECRET = settings.JWT_SECRET or "change-me-access"
REFRESH_SECRET = settings.JWT_REFRESH_SECRET or "change-me-refresh"
ACCESS_MIN = int(os.getenv("ACCESS_MIN", "240"))     # 4 hours
REFRESH_DAYS = int(os.getenv("REFRESH_DAYS", "7"))   # 7 days
# (optional) also export admin creds if other files import them directly
ADMIN_EMAIL = settings.ADMIN_EMAIL
ADMIN_PASSWORD = settings.ADMIN_PASSWORD 
