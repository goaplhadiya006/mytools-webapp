"""
==================================================================
 MAILER.PY
 Email verification / password reset token banavva ane mail
 mokalva mate ni utility.

 IMPORTANT (Gujarati):
 Real email mokalva mate tamare .env file ma tamara Gmail (ke
 bija) SMTP na MAIL_USERNAME / MAIL_PASSWORD nakhva padshe
 (.env.example jovo). Jya sudhi e set nathi karyu tya sudhi,
 app link ne screen upar j batavshe (dev/testing mate) - flow
 tuti nahi jaay.
==================================================================
"""

from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature
from flask import current_app, url_for
from flask_mail import Message

from config import Config


def _serializer():
    return URLSafeTimedSerializer(Config.SECRET_KEY)


def generate_token(email, salt):
    return _serializer().dumps(email, salt=salt)


def confirm_token(token, salt, max_age):
    try:
        email = _serializer().loads(token, salt=salt, max_age=max_age)
    except SignatureExpired:
        return None, "expired"
    except BadSignature:
        return None, "invalid"
    return email, None


def is_mail_configured():
    return bool(Config.MAIL_USERNAME and Config.MAIL_PASSWORD)


def send_email(mail, to, subject, html_body):
    """
    Try to send a real email. Returns True if actually sent.
    If mail is not configured (or sending fails), returns False so
    the caller can fall back to showing the link on screen.
    """
    if not is_mail_configured():
        return False

    try:
        msg = Message(
            subject=subject,
            recipients=[to],
            html=html_body,
            sender=Config.MAIL_DEFAULT_SENDER
        )
        mail.send(msg)
        return True
    except Exception as exc:
        current_app.logger.warning("Mail send failed: %s", exc)
        return False


def build_verification_link(email):
    token = generate_token(email, salt="email-verify")
    if Config.APP_BASE_URL:
        path = url_for("auth.verify_email", token=token)
        return Config.APP_BASE_URL + path
    return url_for("auth.verify_email", token=token, _external=True)


def build_reset_link(email):
    token = generate_token(email, salt="password-reset")
    if Config.APP_BASE_URL:
        path = url_for("auth.reset_password", token=token)
        return Config.APP_BASE_URL + path
    return url_for("auth.reset_password", token=token, _external=True)
