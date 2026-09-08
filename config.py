import os
from dotenv import load_dotenv


# =========================================================
# LOAD ENVIRONMENT VARIABLES
# =========================================================

load_dotenv()


# =========================================================
# BASE DIRECTORY
# =========================================================

BASE_DIR = os.path.dirname(
    os.path.abspath(__file__)
)


class Config:

    # =====================================================
    # SECURITY
    # =====================================================

    SECRET_KEY = os.environ.get(
        "SECRET_KEY",
        "change-this-secret-key-in-production"
    )


    # =====================================================
    # DATABASE (MySQL)
    # =====================================================

    MYSQL_HOST = (
        os.environ.get("MYSQL_HOST")
        or os.environ.get("DB_HOST", "localhost")
    )

    MYSQL_PORT = int(
        os.environ.get("MYSQL_PORT")
        or os.environ.get("DB_PORT", 3306)
    )

    MYSQL_USER = (
        os.environ.get("MYSQL_USER")
        or os.environ.get("DB_USER", "root")
    )

    MYSQL_PASSWORD = (
        os.environ.get("MYSQL_PASSWORD")
        or os.environ.get("DB_PASSWORD", "")
    )

    MYSQL_DATABASE = (
        os.environ.get("MYSQL_DATABASE")
        or os.environ.get("DB_NAME", "mytools_db")
    )


    # =====================================================
    # UPLOAD / PROCESSED FOLDERS
    # =====================================================

    STATIC_FOLDER = os.path.join(
        BASE_DIR,
        "static"
    )

    PROFILE_PICS_FOLDER = os.path.join(
        STATIC_FOLDER,
        "uploads",
        "profile_pics"
    )

    RESIZER_UPLOAD_FOLDER = os.path.join(
        STATIC_FOLDER,
        "uploads",
        "resizer"
    )

    REMOVEBG_UPLOAD_FOLDER = os.path.join(
        STATIC_FOLDER,
        "uploads",
        "removebg"
    )


    # =====================================================
    # ALLOWED IMAGE EXTENSIONS
    # =====================================================

    ALLOWED_IMAGE_EXTENSIONS = {
        "png",
        "jpg",
        "jpeg",
        "webp"
    }


    # =====================================================
    # MAXIMUM REQUEST SIZE
    # =====================================================

    MAX_CONTENT_LENGTH = 20 * 1024 * 1024  # 20 MB


    # =====================================================
    # GMAIL API SETTINGS
    # =====================================================

    # Gmail account used for sending emails.
    # This should be the same Gmail account that you
    # authorized when creating token.json.

    GMAIL_SENDER_EMAIL = os.environ.get(
        "GMAIL_SENDER_EMAIL",
        ""
    )


    # Google OAuth client credentials file.
    #
    # Local:
    # credentials.json
    #
    # Render:
    # Can be configured using environment variable.

    GMAIL_CREDENTIALS_FILE = os.environ.get(
        "GMAIL_CREDENTIALS_FILE",
        "credentials.json"
    )


    # Gmail OAuth token file.
    #
    # Local:
    # token.json
    #
    # Render:
    # We will use GMAIL_TOKEN_JSON environment variable.

    GMAIL_TOKEN_FILE = os.environ.get(
        "GMAIL_TOKEN_FILE",
        "token.json"
    )


    # =====================================================
    # EMAIL LINK BASE URL
    # =====================================================

    # Local:
    # http://127.0.0.1:5000
    #
    # Production:
    # https://mytools-webapp.onrender.com
    #
    # Set APP_BASE_URL in .env / Render Environment Variables.

    APP_BASE_URL = os.environ.get(
        "APP_BASE_URL",
        ""
    ).rstrip("/")


    # =====================================================
    # TOKEN EXPIRY
    # =====================================================

    # Email verification link validity:
    # 24 hours

    EMAIL_VERIFY_EXPIRY_SECONDS = (
        24 * 60 * 60
    )


    # Password reset link validity:
    # 1 hour

    PASSWORD_RESET_EXPIRY_SECONDS = (
        60 * 60
    )

