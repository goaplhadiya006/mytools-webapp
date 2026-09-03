"""
==================================================================
 CONFIG.PY
 Aakha project nu central configuration file.
 Badhu settings (secret key, folders, mail, limits) ahiya che.
==================================================================
"""

import os
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


class Config:

    # -----------------------------------------------------
    # Security
    # -----------------------------------------------------
    SECRET_KEY = os.environ.get("SECRET_KEY", "change-this-secret-key-in-production")

    # -----------------------------------------------------
    # Database (MySQL)
    # Defaults match a typical local XAMPP/MySQL install
    # (host=localhost, user=root, no password). Change these
    # in your .env file to match your real MySQL setup.
    # Also accepts DB_HOST / DB_PORT / DB_USER / DB_PASSWORD /
    # DB_NAME as an alternate naming (either works in .env).
    # -----------------------------------------------------
    MYSQL_HOST = os.environ.get("MYSQL_HOST") or os.environ.get("DB_HOST", "localhost")
    MYSQL_PORT = int(os.environ.get("MYSQL_PORT") or os.environ.get("DB_PORT", 3306))
    MYSQL_USER = os.environ.get("MYSQL_USER") or os.environ.get("DB_USER", "root")
    MYSQL_PASSWORD = os.environ.get("MYSQL_PASSWORD") or os.environ.get("DB_PASSWORD", "")
    MYSQL_DATABASE = os.environ.get("MYSQL_DATABASE") or os.environ.get("DB_NAME", "mytools_db")

    # -----------------------------------------------------
    # Upload / Processed folders
    # -----------------------------------------------------
    STATIC_FOLDER = os.path.join(BASE_DIR, "static")
    PROFILE_PICS_FOLDER = os.path.join(STATIC_FOLDER, "uploads", "profile_pics")
    RESIZER_UPLOAD_FOLDER = os.path.join(STATIC_FOLDER, "uploads", "resizer")
    REMOVEBG_UPLOAD_FOLDER = os.path.join(STATIC_FOLDER, "uploads", "removebg")

    ALLOWED_IMAGE_EXTENSIONS = {"png", "jpg", "jpeg", "webp"}

    MAX_CONTENT_LENGTH = 20 * 1024 * 1024  # 20 MB per request

    # -----------------------------------------------------
    # Mail settings (email verification / password reset)
    # Fill these with your real SMTP provider (e.g. Gmail App Password)
    # in a .env file (see .env.example). If not configured, the app
    # falls back to showing the verification / reset link directly
    # on screen so you can still test everything locally.
    # -----------------------------------------------------
    MAIL_SERVER = os.environ.get("MAIL_SERVER", "smtp.gmail.com")
    MAIL_PORT = int(os.environ.get("MAIL_PORT", 587))
    MAIL_USE_TLS = os.environ.get("MAIL_USE_TLS", "true").lower() == "true"
    MAIL_USERNAME = os.environ.get("MAIL_USERNAME", "")
    MAIL_PASSWORD = os.environ.get("MAIL_PASSWORD", "")
    MAIL_DEFAULT_SENDER = os.environ.get("MAIL_DEFAULT_SENDER", MAIL_USERNAME)

    # -----------------------------------------------------
    # Email links (verification / password reset)
    # By default, links use whatever address you opened the
    # site with in your browser (e.g. http://127.0.0.1:5000).
    # That is FINE if you always open your email on the SAME
    # computer that is running the app.
    #
    # If you open your email on your PHONE (or another device),
    # "127.0.0.1" means that device itself, not your PC - so the
    # link will fail with "connection refused". To fix that, set
    # APP_BASE_URL in .env to your PC's local network address,
    # e.g. APP_BASE_URL=http://192.168.1.5:5000
    # (Find your PC's IP with "ipconfig" on Windows, look for
    # "IPv4 Address"). Leave it empty to use the default behavior.
    # -----------------------------------------------------
    APP_BASE_URL = os.environ.get("APP_BASE_URL", "").rstrip("/")

    # -----------------------------------------------------
    # Token expiry
    # -----------------------------------------------------
    EMAIL_VERIFY_EXPIRY_SECONDS = 24 * 60 * 60      # 24 hours
    PASSWORD_RESET_EXPIRY_SECONDS = 60 * 60         # 1 hour
