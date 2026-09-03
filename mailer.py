import os
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
import requests

from config import Config


# =========================================================
# TOKEN SERIALIZER
# =========================================================

def _serializer():
    return URLSafeTimedSerializer(Config.SECRET_KEY)


# =========================================================
# TOKEN HELPERS
# =========================================================

def _make_token(email, salt):
    return _serializer().dumps(email, salt=salt)


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
    token = _make_token(email, "email-verify")

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
    token = _make_token(email, "password-reset")

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
    return bool(os.environ.get("RESEND_API_KEY"))


# =========================================================
# SEND EMAIL USING RESEND API
# =========================================================

def send_email(mail, to_email, subject, html_content):
    api_key = os.environ.get("RESEND_API_KEY")

    if not api_key:
        print("ERROR: RESEND_API_KEY is not configured.")
        return False

    sender = (
        os.environ.get("MAIL_DEFAULT_SENDER")
        or "onboarding@resend.dev"
    )

    payload = {
        "from": sender,
        "to": [to_email],
        "subject": subject,
        "html": html_content
    }

    try:
        response = requests.post(
            "https://api.resend.com/emails",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            json=payload,
            timeout=30
        )

        if response.status_code in (200, 201):
            print("Email sent successfully.")
            print(response.text)
            return True

        print("Resend email error:")
        print("Status:", response.status_code)
        print("Response:", response.text)

        return False

    except requests.RequestException as e:
        print("Resend API connection error:")
        print(e)
        return False