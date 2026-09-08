import os
import json
import base64

from email.mime.text import MIMEText

from itsdangerous import (
    URLSafeTimedSerializer,
    BadSignature,
    SignatureExpired
)

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

from config import Config


# =========================================================
# GMAIL API
# =========================================================

SCOPES = [
    "https://www.googleapis.com/auth/gmail.send"
]


# =========================================================
# TOKEN SERIALIZER
# =========================================================

def _serializer():
    return URLSafeTimedSerializer(Config.SECRET_KEY)


# =========================================================
# TOKEN HELPERS
# =========================================================

def _make_token(email, salt):
    return _serializer().dumps(
        email,
        salt=salt
    )


def confirm_token(token, salt, max_age):
    try:
        email = _serializer().loads(
            token,
            salt=salt,
            max_age=max_age
        )

        return email, None

    except SignatureExpired:
        return None, "expired"

    except BadSignature:
        return None, "invalid"

    except Exception:
        return None, "invalid"


# =========================================================
# VERIFICATION LINK
# =========================================================

def build_verification_link(email):
    token = _make_token(
        email,
        "email-verify"
    )

    base_url = (
        os.environ.get("APP_BASE_URL")
        or Config.APP_BASE_URL
        or "http://127.0.0.1:5000"
    ).rstrip("/")

    return f"{base_url}/verify-email/{token}"


# =========================================================
# PASSWORD RESET LINK
# =========================================================

def build_reset_link(email):
    token = _make_token(
        email,
        "password-reset"
    )

    base_url = (
        os.environ.get("APP_BASE_URL")
        or Config.APP_BASE_URL
        or "http://127.0.0.1:5000"
    ).rstrip("/")

    return f"{base_url}/reset-password/{token}"


# =========================================================
# MAIL CONFIGURATION CHECK
# =========================================================

def is_mail_configured():

    # Local development:
    # token.json must exist.

    local_token = getattr(
        Config,
        "GMAIL_TOKEN_FILE",
        "token.json"
    )

    if os.path.exists(local_token):
        return True

    # Render / production:
    # Gmail token can be stored in environment variable.

    return bool(
        os.environ.get("GMAIL_TOKEN_JSON")
    )


# =========================================================
# LOAD GMAIL CREDENTIALS
# =========================================================

def _load_gmail_credentials():

    token_json = os.environ.get(
        "GMAIL_TOKEN_JSON"
    )

    # -----------------------------------------------------
    # Render / Production
    # -----------------------------------------------------

    if token_json:

        try:

            token_data = json.loads(
                token_json
            )

            creds = Credentials.from_authorized_user_info(
                token_data,
                SCOPES
            )

            print(
                "Gmail credentials loaded from environment."
            )

        except Exception as e:

            print(
                "ERROR: Invalid GMAIL_TOKEN_JSON."
            )

            print(str(e))

            return None

    # -----------------------------------------------------
    # Local Development
    # -----------------------------------------------------

    else:

        token_file = getattr(
            Config,
            "GMAIL_TOKEN_FILE",
            "token.json"
        )

        if not os.path.exists(token_file):

            print(
                "ERROR: token.json not found."
            )

            print(
                "Run gmail_auth.py first."
            )

            return None

        try:

            creds = Credentials.from_authorized_user_file(
                token_file,
                SCOPES
            )

            print(
                "Gmail credentials loaded from token.json."
            )

        except Exception as e:

            print(
                "ERROR: Could not load token.json."
            )

            print(str(e))

            return None

    # -----------------------------------------------------
    # Refresh expired access token
    # -----------------------------------------------------

    try:

        if creds.expired and creds.refresh_token:

            print(
                "Gmail access token expired."
            )

            print(
                "Refreshing Gmail access token..."
            )

            creds.refresh(
                Request()
            )

            print(
                "Gmail access token refreshed."
            )

    except Exception as e:

        print(
            "ERROR: Gmail token refresh failed."
        )

        print(str(e))

        return None

    return creds


# =========================================================
# SEND EMAIL USING GMAIL API
# =========================================================

def send_email(
    mail,
    to_email,
    subject,
    html_content
):

    print(
        "\n========== GMAIL API EMAIL DEBUG =========="
    )

    print(
        "Recipient:",
        to_email
    )

    print(
        "Subject:",
        subject
    )

    print(
        "==========================================="
    )

    # -----------------------------------------------------
    # Load Gmail credentials
    # -----------------------------------------------------

    creds = _load_gmail_credentials()

    if not creds:

        print(
            "ERROR: Gmail credentials are not available."
        )

        return False

    try:

        # -------------------------------------------------
        # Create Gmail API service
        # -------------------------------------------------

        service = build(
            "gmail",
            "v1",
            credentials=creds,
            cache_discovery=False
        )

        # -------------------------------------------------
        # Create HTML email
        # -------------------------------------------------

        message = MIMEText(
            html_content,
            "html",
            "utf-8"
        )

        message["To"] = to_email
        message["Subject"] = subject

        sender = (
            os.environ.get("GMAIL_SENDER_EMAIL")
            or getattr(
                Config,
                "GMAIL_SENDER_EMAIL",
                ""
            )
        )

        if sender:
            message["From"] = sender

        # -------------------------------------------------
        # Encode email
        # -------------------------------------------------

        raw_message = base64.urlsafe_b64encode(
            message.as_bytes()
        ).decode()

        body = {
            "raw": raw_message
        }

        # -------------------------------------------------
        # Send email
        # -------------------------------------------------

        result = (
            service
            .users()
            .messages()
            .send(
                userId="me",
                body=body
            )
            .execute()
        )

        print(
            "========== GMAIL API RESPONSE =========="
        )

        print(
            "Message ID:",
            result.get("id")
        )

        print(
            "Email sent successfully."
        )

        print(
            "========================================="
        )

        return True

    except Exception as e:

        print(
            "========== GMAIL API ERROR =========="
        )

        print(
            "Email sending failed."
        )

        print(
            "Error:",
            str(e)
        )

        print(
            "====================================="
        )

        return False

