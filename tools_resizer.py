"""
==================================================================
 TOOLS_RESIZER.PY
 "Image Resizer - Compressor" tool - login pachi j vaparva madse.

 Aa core processing logic (EXIF orientation, safe resize, format
 conversion, decompression-bomb safety limits) tamara uploaded
 "Image Resizer - Compressor" standalone project mathi j lidhu
 che - same to same. Ek j sathe multiple images upload kari
 shakay (bulk), badha resize/compress thay, ane ek ZIP ma
 download thay - jem standalone tool ma hatu tem j.

 Farak fakt etlo j che: aa version login required che, dareek
 user ni files alag user-folder ma save thay, ane history
 MySQL database ma save thay.
==================================================================
"""

import os
import uuid
import shutil
import zipfile
import gc
import warnings

from flask import (
    Blueprint, render_template, request, send_from_directory, flash
)
from PIL import Image, ImageOps, UnidentifiedImageError
from werkzeug.utils import secure_filename

import db
from auth import login_required, current_user
from config import Config

resizer_bp = Blueprint("resizer", __name__)

ALLOWED_FORMATS = {"JPEG": "jpg", "PNG": "png", "WEBP": "webp"}

# ------------------------------------------------------------
# Safety limits (same values as the standalone tool) so very
# large images can't crash the server / eat all the RAM.
# ------------------------------------------------------------
MAX_SOURCE_PIXELS = 12_000_000
MAX_OUTPUT_PIXELS = 8_000_000
MAX_DIMENSION = 4000
MAX_FILES_PER_REQUEST = 10

Image.MAX_IMAGE_PIXELS = MAX_SOURCE_PIXELS
warnings.simplefilter("error", Image.DecompressionBombWarning)


def _allowed_image(filename):
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower() in Config.ALLOWED_IMAGE_EXTENSIONS
    )


def _user_folder(user_id):
    folder = os.path.join(Config.RESIZER_UPLOAD_FOLDER, str(user_id))
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


def _convert_for_output(image, output_format):
    if output_format == "JPEG":
        if image.mode == "RGB":
            return image
        if image.mode == "RGBA":
            background = Image.new("RGB", image.size, "white")
            background.paste(image, mask=image.getchannel("A"))
            return background
        return image.convert("RGB")

    if output_format == "PNG":
        if image.mode in ("RGB", "RGBA"):
            return image
        return image.convert("RGBA")

    if output_format == "WEBP":
        if image.mode in ("RGB", "RGBA"):
            return image
        return image.convert("RGB")

    return image


def _process_single_image(source_path, output_path, width, height, quality, output_format):
    """
    Memory-conscious single image resize + compress.
    Mirrors the standalone tool's process_single_image().
    """
    source_image = None
    resized_image = None
    output_image = None

    try:
        source_image = Image.open(source_path)
        source_width, source_height = source_image.size
        source_pixels = source_width * source_height

        if source_pixels > MAX_SOURCE_PIXELS:
            raise ValueError(
                "This image is too large to process safely. "
                f"Maximum supported image size is {MAX_SOURCE_PIXELS:,} pixels."
            )

        try:
            source_image = ImageOps.exif_transpose(source_image)
        except Exception:
            pass

        if source_image.mode in ("RGBA", "LA", "P"):
            source_image = source_image.convert("RGBA")
        else:
            source_image = source_image.convert("RGB")

        resized_image = source_image.resize((width, height), Image.Resampling.LANCZOS)
        output_image = _convert_for_output(resized_image, output_format)

        if output_format == "JPEG":
            output_image.save(output_path, "JPEG", quality=quality, optimize=True, progressive=True)
        elif output_format == "PNG":
            output_image.save(output_path, "PNG", optimize=True)
        elif output_format == "WEBP":
            output_image.save(output_path, "WEBP", quality=quality, method=4)
        else:
            raise ValueError("Unsupported output format.")

        if not os.path.exists(output_path):
            raise RuntimeError("Processed image was not created.")

        processed_size = os.path.getsize(output_path)
        if processed_size <= 0:
            raise RuntimeError("Processed image is empty.")

        return processed_size

    finally:
        for img in (source_image, resized_image, output_image):
            try:
                if img is not None:
                    img.close()
            except Exception:
                pass
        gc.collect()


def _validate_dimensions(width, height):
    if width <= 0 or height <= 0:
        return False, "Width and height must be greater than 0."
    if width > MAX_DIMENSION:
        return False, f"Maximum width allowed is {MAX_DIMENSION}px."
    if height > MAX_DIMENSION:
        return False, f"Maximum height allowed is {MAX_DIMENSION}px."
    if width * height > MAX_OUTPUT_PIXELS:
        return False, f"Requested output is too large. Maximum supported output is {MAX_OUTPUT_PIXELS:,} pixels."
    return True, ""


@resizer_bp.route("/tools/resizer", methods=["GET"])
@login_required
def resizer_page():
    return render_template("resizer.html")


@resizer_bp.route("/tools/resizer/process", methods=["POST"])
@login_required
def resizer_process():
    user = current_user()

    files = [f for f in request.files.getlist("images") if f and f.filename]
    # Backward compatible single-file field name too.
    if not files and "image" in request.files and request.files["image"].filename:
        files = [request.files["image"]]

    if not files:
        flash("Please select at least one image.", "error")
        return render_template("resizer.html"), 400

    if len(files) > MAX_FILES_PER_REQUEST:
        flash(f"You can process up to {MAX_FILES_PER_REQUEST} images at a time.", "error")
        return render_template("resizer.html"), 400

    width_in = request.form.get("width", type=int)
    height_in = request.form.get("height", type=int)
    quality = request.form.get("quality", default=80, type=int)
    out_format = (request.form.get("format") or "JPEG").upper()

    if out_format not in ALLOWED_FORMATS:
        out_format = "JPEG"
    quality = max(10, min(quality, 100))

    batch_id = uuid.uuid4().hex
    folder = _batch_folder(user["id"], batch_id)

    results = []
    total_original = 0
    total_processed = 0

    for file in files:
        if not _allowed_image(file.filename):
            results.append({"filename": file.filename, "success": False,
                             "error": "Invalid format. Use PNG, JPG, JPEG or WEBP."})
            continue

        safe_name = secure_filename(file.filename)
        unique_id = uuid.uuid4().hex
        tmp_source = os.path.join(folder, f"src_{unique_id}_{safe_name}")

        try:
            file.save(tmp_source)
            original_size = os.path.getsize(tmp_source)

            probe = Image.open(tmp_source)
            probe = ImageOps.exif_transpose(probe)
            ow, oh = probe.size
            probe.close()

            width, height = width_in, height_in
            if not width and not height:
                width, height = ow, oh
            elif width and not height:
                height = int(oh * (width / ow))
            elif height and not width:
                width = int(ow * (height / oh))

            ok, msg = _validate_dimensions(width, height)
            if not ok:
                results.append({"filename": safe_name, "success": False, "error": msg})
                os.remove(tmp_source)
                continue

            ext = ALLOWED_FORMATS[out_format]
            output_filename = f"{unique_id}_resized.{ext}"
            output_path = os.path.join(folder, output_filename)

            processed_size = _process_single_image(
                tmp_source, output_path, width, height, quality, out_format
            )

            os.remove(tmp_source)

            db.add_history(
                user_id=user["id"], tool="resizer", operation="resize_compress",
                processed_filename=output_filename, original_filename=safe_name,
                file_size=processed_size, batch_id=batch_id
            )

            total_original += original_size
            total_processed += processed_size

            results.append({
                "filename": output_filename,
                "original_name": safe_name,
                "success": True,
                "size": _format_size(processed_size),
                "dimensions": f"{width} x {height}"
            })

        except UnidentifiedImageError:
            results.append({"filename": file.filename, "success": False, "error": "Not a valid image file."})
            if os.path.exists(tmp_source):
                os.remove(tmp_source)
        except Exception as exc:
            results.append({"filename": file.filename, "success": False, "error": str(exc)})
            if os.path.exists(tmp_source):
                os.remove(tmp_source)

    successful = [r for r in results if r["success"]]
    zip_name = None

    if len(successful) > 1:
        zip_name = f"resized_images_{batch_id}.zip"
        zip_path = os.path.join(folder, zip_name)
        try:
            with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as zf:
                for r in successful:
                    zf.write(os.path.join(folder, r["filename"]), arcname=r["filename"])
        except Exception:
            zip_name = None

    saved_percent = 0
    if total_original > 0:
        saved_percent = round((total_original - total_processed) / total_original * 100, 2)

    if not successful:
        flash("None of the images could be processed. Please check the errors below.", "error")

    return render_template(
        "resizer.html",
        results=results,
        batch_id=batch_id,
        zip_name=zip_name,
        file_count=len(successful),
        saved_percent=saved_percent
    )


@resizer_bp.route("/tools/resizer/file/<batch_id>/<filename>")
@login_required
def resizer_file(batch_id, filename):
    user = current_user()
    batch_id = secure_filename(batch_id)
    filename = secure_filename(filename)
    return send_from_directory(_batch_folder(user["id"], batch_id), filename)


@resizer_bp.route("/tools/resizer/download-zip/<batch_id>")
@login_required
def resizer_download_zip(batch_id):
    user = current_user()
    batch_id = secure_filename(batch_id)
    folder = _batch_folder(user["id"], batch_id)
    zip_name = f"resized_images_{batch_id}.zip"
    zip_path = os.path.join(folder, zip_name)

    if not os.path.isfile(zip_path):
        flash("Zip file not found. It may have expired.", "error")
        return render_template("resizer.html"), 404

    return send_from_directory(folder, zip_name, as_attachment=True)
