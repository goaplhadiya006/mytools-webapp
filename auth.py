"""
==================================================================
 AUTH.PY
 Signup, Email Verification, Login, Logout,
 Forgot Password, Reset Password - badhu ahiya.

 Server-side validation j final validation che (JS client-side
 mate che, pan security mate server upar j re-check thay che).
==================================================================
"""

import re
from functools import wraps

from flask import (
    Blueprint, render_template, request, redirect,
    url_for, session, flash, current_app
)
from werkzeug.security import generate_password_hash, check_password_hash

import db
from mailer import (
    send_email, build_verification_link, build_reset_link,
    confirm_token, is_mail_configured
)
from config import Config

auth_bp = Blueprint("auth", __name__)


# =========================================================
# VALIDATION HELPERS (server-side, source of truth)
# =========================================================

EMAIL_REGEX = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
NAME_REGEX = re.compile(r"^[A-Za-z ]{2,40}$")

# min 8 chars, 1 uppercase, 1 lowercase, 1 number, 1 special char
PASSWORD_REGEX = re.compile(
    r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[!@#$%^&*()_\-+=\[\]{}|;:,.<>?]).{8,}$"
)


def validate_signup(first_name, last_name, email, password, confirm_password):
    errors = {}

    if not first_name or not NAME_REGEX.match(first_name.strip()):
        errors["first_name"] = "First name only letters, 2-40 characters."

    if not last_name or not NAME_REGEX.match(last_name.strip()):
        errors["last_name"] = "Last name only letters, 2-40 characters."

    if not email or not EMAIL_REGEX.match(email.strip()):
        errors["email"] = "Please enter a valid email address."

    if not password or not PASSWORD_REGEX.match(password):
        errors["password"] = (
            "Password must be 8+ characters and include uppercase, "
            "lowercase, number and special character."
        )

    if password != confirm_password:
        errors["confirm_password"] = "Passwords do not match."

    return errors


# =========================================================
# LOGIN REQUIRED DECORATOR
# =========================================================

def login_required(view_func):
    @wraps(view_func)
    def wrapper(*args, **kwargs):
        if not session.get("user_id"):
            flash("Please login first.", "error")
            return redirect(url_for("auth.login"))
        return view_func(*args, **kwargs)
    return wrapper


def current_user():
    user_id = session.get("user_id")
    if not user_id:
        return None
    return db.get_user_by_id(user_id)


# =========================================================
# SIGNUP
# =========================================================

@auth_bp.route("/signup", methods=["GET", "POST"])
def signup():
    if session.get("user_id"):
        return redirect(url_for("dashboard"))

    if request.method == "GET":
        return render_template("signup.html")

    first_name = (request.form.get("first_name") or "").strip()
    last_name = (request.form.get("last_name") or "").strip()
    email = (request.form.get("email") or "").strip().lower()
    password = request.form.get("password") or ""
    confirm_password = request.form.get("confirm_password") or ""

    errors = validate_signup(first_name, last_name, email, password, confirm_password)

    if not errors and db.get_user_by_email(email):
        errors["email"] = "This email is already registered."

    if errors:
        return render_template(
            "signup.html", errors=errors,
            first_name=first_name, last_name=last_name, email=email
        ), 400

    password_hash = generate_password_hash(password)
    user_id = db.create_user(first_name, last_name, email, password_hash)

    link = build_verification_link(email)
    html = render_template("email_verify.html", first_name=first_name, link=link)
    sent = send_email(current_app.extensions["mail"], email,
                       "Verify your account", html)

    return render_template(
        "verify_notice.html",
        email=email,
        sent=sent,
        # Link ne hammesha batavay che (fallback), kem ke real inbox ma
        # delay thai shake ke spam ma jai shake - user atki na jay etle.
        dev_link=link
    )


# =========================================================
# EMAIL VERIFICATION
# =========================================================

@auth_bp.route("/verify-email/<token>")
def verify_email(token):
    email, error = confirm_token(
        token, salt="email-verify",
        max_age=Config.EMAIL_VERIFY_EXPIRY_SECONDS
    )

    if error == "expired":
        flash("Verification link has expired. Please sign up again or request a new link.", "error")
        return redirect(url_for("auth.login"))

    if error == "invalid" or not email:
        flash("Invalid verification link.", "error")
        return redirect(url_for("auth.login"))

    user = db.get_user_by_email(email)
    if not user:
        flash("Account not found.", "error")
        return redirect(url_for("auth.signup"))

    if not user["is_verified"]:
        db.mark_user_verified(user["id"])

    return render_template("verify_success.html")


# =========================================================
# LOGIN
# =========================================================

@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    # Requirement: agar user already login thayelo hoy, to login
    # page pachu dekhadvu nahi - seedhu dashboard par mokli devu.
    # Login karyu, koi bija tab/URL thi /login kholva ni koshish
    # karshe to pan e dashboard par j jashe. Logout karya pachi
    # session clear thai jashe, etle tyare login page barabar
    # khulshe.
    if session.get("user_id"):
        return redirect(url_for("dashboard"))

    if request.method == "GET":
        return render_template("login.html")

    email = (request.form.get("email") or "").strip().lower()
    password = request.form.get("password") or ""

    errors = {}
    user = db.get_user_by_email(email)

    if not user or not check_password_hash(user["password_hash"], password):
        errors["general"] = "Invalid email or password."
        return render_template("login.html", errors=errors, email=email), 400

    if not user["is_verified"]:
        errors["general"] = "Please verify your email before logging in."
        return render_template("login.html", errors=errors, email=email), 400

    session["user_id"] = user["id"]
    session["user_name"] = user["first_name"]
    flash("Logged in successfully.", "success")
    return redirect(url_for("dashboard"))


@auth_bp.route("/logout")
def logout():
    session.clear()
    flash("Logged out.", "success")
    return redirect(url_for("auth.login"))


# =========================================================
# FORGOT PASSWORD
# =========================================================

@auth_bp.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    if request.method == "GET":
        return render_template("forgot_password.html")

    email = (request.form.get("email") or "").strip().lower()

    if not email or not EMAIL_REGEX.match(email):
        return render_template(
            "forgot_password.html",
            errors={"email": "Please enter a valid email address."},
            email=email
        ), 400

    user = db.get_user_by_email(email)

    # Security: don't reveal whether the email exists or not.
    dev_link = None
    sent = False

    if user:
        link = build_reset_link(email)
        html = render_template(
            "email_reset.html", first_name=user["first_name"], link=link
        )
        sent = send_email(current_app.extensions["mail"], email,
                           "Reset your password", html)
        # Link ne hammesha fallback tarike batavay che (delay/spam
        # thai shake tevi situation mate) - user atki na jay etle.
        dev_link = link

    return render_template("forgot_password_sent.html", sent=sent, dev_link=dev_link)


# =========================================================
# RESET PASSWORD (from email link)
# =========================================================

@auth_bp.route("/reset-password/<token>", methods=["GET", "POST"])
def reset_password(token):
    email, error = confirm_token(
        token, salt="password-reset",
        max_age=Config.PASSWORD_RESET_EXPIRY_SECONDS
    )

    if error == "expired":
        flash("Reset link has expired. Please request a new one.", "error")
        return redirect(url_for("auth.forgot_password"))

    if error == "invalid" or not email:
        flash("Invalid reset link.", "error")
        return redirect(url_for("auth.forgot_password"))

    user = db.get_user_by_email(email)
    if not user:
        flash("Account not found.", "error")
        return redirect(url_for("auth.forgot_password"))

    if request.method == "GET":
        return render_template("reset_password.html", token=token)

    new_password = request.form.get("new_password") or ""
    confirm_password = request.form.get("confirm_password") or ""

    errors = {}
    if not PASSWORD_REGEX.match(new_password):
        errors["new_password"] = (
            "Password must be 8+ characters and include uppercase, "
            "lowercase, number and special character."
        )
    if new_password != confirm_password:
        errors["confirm_password"] = "Passwords do not match."

    if errors:
        return render_template("reset_password.html", token=token, errors=errors), 400

    db.update_user_password(user["id"], generate_password_hash(new_password))
    flash("Password has been reset. Please login with your new password.", "success")
    return redirect(url_for("auth.login"))
