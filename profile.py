"""
==================================================================
 PROFILE.PY
 Profile page: naam edit, profile picture upload, ane
 "Reset Password" (old password + new password) - login thai
 gaya pachi ni account settings.
==================================================================
"""

import os
import uuid

from flask import (
    Blueprint, render_template, request, redirect,
    url_for, flash, session
)
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash

import db
from auth import login_required, current_user, NAME_REGEX, PASSWORD_REGEX
from config import Config

profile_bp = Blueprint("profile", __name__)


def _allowed_image(filename):
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower() in Config.ALLOWED_IMAGE_EXTENSIONS
    )


@profile_bp.route("/profile", methods=["GET"])
@login_required
def profile_page():
    user = current_user()
    return render_template("profile.html", user=user)


# =========================================================
# UPDATE NAME
# =========================================================

@profile_bp.route("/profile/update", methods=["POST"])
@login_required
def update_profile():
    user = current_user()

    first_name = (request.form.get("first_name") or "").strip()
    last_name = (request.form.get("last_name") or "").strip()

    errors = {}
    if not first_name or not NAME_REGEX.match(first_name):
        errors["first_name"] = "First name only letters, 2-40 characters."
    if not last_name or not NAME_REGEX.match(last_name):
        errors["last_name"] = "Last name only letters, 2-40 characters."

    if errors:
        return render_template("profile.html", user=user, errors=errors), 400

    db.update_profile_names(user["id"], first_name, last_name)
    session["user_name"] = first_name
    flash("Profile updated successfully.", "success")
    return redirect(url_for("profile.profile_page"))


# =========================================================
# UPLOAD PROFILE PICTURE
# =========================================================

@profile_bp.route("/profile/upload-picture", methods=["POST"])
@login_required
def upload_picture():
    user = current_user()

    if "profile_image" not in request.files or request.files["profile_image"].filename == "":
        flash("Please choose an image to upload.", "error")
        return redirect(url_for("profile.profile_page"))

    file = request.files["profile_image"]

    if not _allowed_image(file.filename):
        flash("Invalid image format. Use PNG, JPG, JPEG or WEBP.", "error")
        return redirect(url_for("profile.profile_page"))

    os.makedirs(Config.PROFILE_PICS_FOLDER, exist_ok=True)

    ext = secure_filename(file.filename).rsplit(".", 1)[1].lower()
    filename = f"user{user['id']}_{uuid.uuid4().hex}.{ext}"
    file.save(os.path.join(Config.PROFILE_PICS_FOLDER, filename))

    # remove old picture (exercise: replace old with new)
    if user["profile_image"]:
        old_path = os.path.join(Config.PROFILE_PICS_FOLDER, user["profile_image"])
        if os.path.isfile(old_path):
            try:
                os.remove(old_path)
            except OSError:
                pass

    db.update_profile_image(user["id"], filename)
    flash("Profile picture updated.", "success")
    return redirect(url_for("profile.profile_page"))


@profile_bp.route("/profile/remove-picture", methods=["POST"])
@login_required
def remove_picture():
    user = current_user()

    if user["profile_image"]:
        old_path = os.path.join(Config.PROFILE_PICS_FOLDER, user["profile_image"])
        if os.path.isfile(old_path):
            try:
                os.remove(old_path)
            except OSError:
                pass
        db.update_profile_image(user["id"], None)
        flash("Profile picture removed.", "success")

    return redirect(url_for("profile.profile_page"))


# =========================================================
# CHANGE PASSWORD (old password + new password)
# =========================================================

@profile_bp.route("/profile/change-password", methods=["POST"])
@login_required
def change_password():
    user = current_user()

    old_password = request.form.get("old_password") or ""
    new_password = request.form.get("new_password") or ""
    confirm_password = request.form.get("confirm_password") or ""

    errors = {}

    if not check_password_hash(user["password_hash"], old_password):
        errors["old_password"] = "Old password is incorrect."

    if not PASSWORD_REGEX.match(new_password):
        errors["new_password"] = (
            "Password must be 8+ characters and include uppercase, "
            "lowercase, number and special character."
        )

    if new_password != confirm_password:
        errors["confirm_password"] = "Passwords do not match."

    if not errors and check_password_hash(user["password_hash"], new_password):
        errors["new_password"] = "New password must be different from old password."

    if errors:
        return render_template("profile.html", user=user, pw_errors=errors), 400

    db.update_user_password(user["id"], generate_password_hash(new_password))
    flash("Password changed successfully.", "success")
    return redirect(url_for("profile.profile_page"))
