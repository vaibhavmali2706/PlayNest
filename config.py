"""
PlayNest configuration.

All settings are read from environment variables so the app is
production-ready and database-ready without code changes: swap the
mock repositories in services/ for real ones and point MAIL_* / a
DATABASE_URL at real infrastructure whenever that work is scheduled.
"""

import os
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


class Config:
    SECRET_KEY = os.environ["SECRET_KEY"]
    DEBUG = os.environ.get("FLASK_DEBUG", "False").lower() == "true"

    # ---- Session ----
    SESSION_COOKIE_HTTPONLY = True
    PERMANENT_SESSION_LIFETIME = 60 * 60 * 24  # 24 hours

    # ---- Mail ----
    MAIL_SERVER = os.environ.get("MAIL_SERVER", "smtp.gmail.com")
    MAIL_PORT = int(os.environ.get("MAIL_PORT", 587))
    MAIL_USE_TLS = os.environ.get("MAIL_USE_TLS", "True") == "True"
    MAIL_USERNAME = os.environ.get("MAIL_USERNAME")
    MAIL_PASSWORD = os.environ.get("MAIL_PASSWORD")
    MAIL_DEFAULT_SENDER = os.environ.get(
        "MAIL_DEFAULT_SENDER", "PlayNest <no-reply@playnest.app>"
    )

    # PlayNest is considered "wired for real email" only when credentials
    # are actually present. Otherwise it degrades gracefully to DEV MODE.
    MAIL_CONFIGURED = bool(MAIL_USERNAME and MAIL_PASSWORD)

    # ---- OTP policy ----
    OTP_LENGTH = 6
    OTP_VALID_MINUTES = 5
    OTP_MAX_ATTEMPTS = 5
    OTP_RESEND_SECONDS = 30

    # ---- Admin policy ----
    ADMIN_PASSCODE = os.environ.get("ADMIN_PASSCODE", "270607")

    # ---- Booking policy ----
    CANCELLATION_WINDOW_HOURS = 3

    # ---- Database readiness flag ----
    # Every service in services/ is written against small repository
    # interfaces so flipping this (and swapping the repository
    # implementation) is the only step needed to go live on a real DB.
    DATABASE_READY = os.environ.get("DATABASE_READY", "False") == "True"

    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL")
    if SQLALCHEMY_DATABASE_URI:
        if SQLALCHEMY_DATABASE_URI.startswith("postgresql://"):
            SQLALCHEMY_DATABASE_URI = SQLALCHEMY_DATABASE_URI.replace("postgresql://", "postgresql+pg8000://", 1)
        elif SQLALCHEMY_DATABASE_URI.startswith("postgres://"):
            SQLALCHEMY_DATABASE_URI = SQLALCHEMY_DATABASE_URI.replace("postgres://", "postgresql+pg8000://", 1)
    else:
        SQLALCHEMY_DATABASE_URI = f"sqlite:///{os.path.join(BASE_DIR, 'playnest.db')}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False


