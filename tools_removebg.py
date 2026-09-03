"""
==================================================================
 TOOLS_REMOVEBG.PY
 "RemoveBG Pro" tool - login pachi j vaparva madse.

 Background removal logic (rembg + u2net model, max 1500px
 processing size, optional solid color background) tamara
 uploaded "RemoveBG Pro" standalone project mathi j lidhu che -
 same to same. Ek j sathe multiple images upload kari shakay
 (bulk), badhi ni background remove thay, ane ek ZIP ma
 download thay - jem standalone tool ma hatu tem j.

 Farak fakt etlo j che: aa version login required che, dareek
 user ni files alag user-folder ma save thay, ane history
 MySQL database ma save thay.
==================================================================
"""

import os
import uuid
import zipfile

from flask import (
    Blueprint, render_template, request, send_from_directory, flash
)
from PIL import Image
from werkzeug.utils import secure_filename

import db
from auth import login_required, current_user
from config import Config

removebg_bp = Blueprint("removebg", __name__)

MAX_FILES_PER_REQUEST = 10
MAX_PROCESS_DIMENSION = 1500  # same as standalone tool

_session = None  # rembg session, lazy-loaded (heavy AI model)


def _get_session():
    global _session
    if _session is None:
        from rembg import new_session
        _session = new_session("u2net")
    return _session


def _allowed_image(filename):
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower() in Config.ALLOWED_IMAGE_EXTENSIONS
    )


def _user_folder(user_id):
    folder = os.path.join(Config.REMOVEBG_UPLOAD_FOLDER, str(user_id))
    os.makedirs(folder, exist_ok=True)
    return folder


def _batch_folder(user_id, batch_id):
    folder = os.path.join(_user_folder(user_id), batch_id)
    os.makedirs(folder, exist_ok=True)
    return folder


def _format_size(size):
    if not size:
        return "0 B"
    if size < 1024:
        return f"{size} B"
    if size < 1024 * 1024:
        return f"{size / 1024:.2f} KB"
    return f"{size / (1024 * 1024):.2f} MB"


def _valid_hex_color(color):
    if not isinstance(color, str) or len(color) != 7 or not color.startswith("#"):
        return False
    try:
        int(color[1:], 16)
        return True
    except ValueError:
        return False


def _remove_background_single(input_path, output_path, bg_color=None):
    """
    Mirrors the standalone tool's remove_background(): resize down
    to a safe max dimension before running the AI model (memory
    safety), run rembg with the u2net session, then optionally
    composite a solid background color.
    """
    from rembg import remove

    image = None
    processing_image = None
    output_image = None
    background = None

    try:
        image = Image.open(input_path).convert("RGBA")
        w, h = image.size

        if max(w, h) > MAX_PROCESS_DIMENSION:
            scale = MAX_PROCESS_DIMENSION / max(w, h)
            processing_image = image.resize(
                (int(w * scale), int(h * scale)), Image.Resampling.LANCZOS
            )
        else:
            processing_image = image.copy()

        output_image = remove(processing_image, session=_get_session()).convert("RGBA")

        if bg_color and _valid_hex_color(bg_color):
            background = Image.new("RGBA", output_image.size, bg_color)
            composited = Image.alpha_composite(background, output_image)
            output_image.close()
            output_image = composited

        output_image.save(output_path, "PNG")

    finally:
        for img in (output_image, processing_image, image, background):
            try:
                if img is not None:
                    img.close()
            except Exception:
                pass


@removebg_bp.route("/tools/removebg", methods=["GET"])
@login_required
def removebg_page():
    return render_template("removebg.html")


@removebg_bp.route("/tools/removebg/process", methods=["POST"])
@login_required
def removebg_process():
    user = current_user()

    files = [f for f in request.files.getlist("images") if f and f.filename]
    if not files and "image" in request.files and request.files["image"].filename:
        files = [request.files["image"]]

    if not files:
        flash("Please select at least one image.", "error")
        return render_template("removebg.html"), 400

    if len(files) > MAX_FILES_PER_REQUEST:
        flash(f"You can process up to {MAX_FILES_PER_REQUEST} images at a time.", "error")
        return render_template("removebg.html"), 400

    bg_color = request.form.get("bg_color")
    if bg_color and not _valid_hex_color(bg_color):
        bg_color = None

    batch_id = uuid.uuid4().hex
    folder = _batch_folder(user["id"], batch_id)

    results = []

    for file in files:
        if not _allowed_image(file.filename):
            results.append({"filename": file.filename, "success": False,
                             "error": "Invalid format. Use PNG, JPG, JPEG or WEBP."})
            continue

        safe_name = secure_filename(file.filename)
        unique_id = uuid.uuid4().hex
        input_path = os.path.join(folder, f"src_{unique_id}_{safe_name}")
        output_filename = f"{unique_id}_removed.png"
        output_path = os.path.join(folder, output_filename)

        try:
            file.save(input_path)
            _remove_background_single(input_path, output_path, bg_color)
            # Note: source image (input_path) is kept in the batch folder
            # (not deleted) so the before/after comparison can show it.

            file_size = os.path.getsize(output_path)

            db.add_history(
                user_id=user["id"], tool="removebg", operation="remove_background",
                processed_filename=output_filename, original_filename=safe_name,
                file_size=file_size, batch_id=batch_id
            )

            results.append({
                "filename": output_filename,
                "source_filename": os.path.basename(input_path),
                "original_name": safe_name,
                "success": True,
                "size": _format_size(file_size)
            })

        except Exception as exc:
            if os.path.exists(input_path):
                os.remove(input_path)
            if os.path.exists(output_path):
                os.remove(output_path)
            results.append({"filename": file.filename, "success": False, "error": str(exc)})

    successful = [r for r in results if r["success"]]
    zip_name = None

    if len(successful) > 1:
        zip_name = f"removebg_images_{batch_id}.zip"
        zip_path = os.path.join(folder, zip_name)
        try:
            with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
                for r in successful:
                    zf.write(os.path.join(folder, r["filename"]), arcname=r["filename"])
        except Exception:
            zip_name = None

    if not successful:
        flash("None of the images could be processed. Please check the errors below.", "error")

    return render_template(
        "removebg.html",
        results=results,
        batch_id=batch_id,
        zip_name=zip_name,
        file_count=len(successful)
    )


@removebg_bp.route("/tools/removebg/file/<batch_id>/<filename>")
@login_required
def removebg_file(batch_id, filename):
    user = current_user()
    batch_id = secure_filename(batch_id)
    filename = secure_filename(filename)
    return send_from_directory(_batch_folder(user["id"], batch_id), filename)


@removebg_bp.route("/tools/removebg/download-zip/<batch_id>")
@login_required
def removebg_download_zip(batch_id):
    user = current_user()
    batch_id = secure_filename(batch_id)
    folder = _batch_folder(user["id"], batch_id)
    zip_name = f"removebg_images_{batch_id}.zip"
    zip_path = os.path.join(folder, zip_name)

    if not os.path.isfile(zip_path):
        flash("Zip file not found. It may have expired.", "error")
        return render_template("removebg.html"), 404

    return send_from_directory(folder, zip_name, as_attachment=True)
