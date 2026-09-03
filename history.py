"""
==================================================================
 HISTORY.PY
 Badha tools ni history ek j jagya ae - delete single image,
 delete all history.
==================================================================
"""

import os

from flask import Blueprint, render_template, redirect, url_for, flash

import db
from auth import login_required, current_user
from config import Config

history_bp = Blueprint("history", __name__)


def _folder_for(tool, user_id):
    if tool == "resizer":
        base = Config.RESIZER_UPLOAD_FOLDER
    else:
        base = Config.REMOVEBG_UPLOAD_FOLDER
    return os.path.join(base, str(user_id))


def _format_size(size):
    if not size:
        return "0 B"
    if size < 1024:
        return f"{size} B"
    if size < 1024 * 1024:
        return f"{size / 1024:.2f} KB"
    return f"{size / (1024 * 1024):.2f} MB"


@history_bp.route("/history")
@login_required
def history_page():
    user = current_user()
    records = db.get_history_for_user(user["id"])

    items = []
    for r in records:
        folder = _folder_for(r["tool"], user["id"])
        batch_id = r["batch_id"]
        file_folder = os.path.join(folder, batch_id) if batch_id else folder
        exists = bool(batch_id) and os.path.isfile(os.path.join(file_folder, r["processed_filename"]))
        items.append({
            "id": r["id"],
            "tool": r["tool"],
            "operation": r["operation"],
            "original_filename": r["original_filename"],
            "processed_filename": r["processed_filename"],
            "display_size": _format_size(r["file_size"]),
            "created_at": r["created_at"],
            "exists": exists,
            "url": url_for(
                f"{'resizer' if r['tool'] == 'resizer' else 'removebg'}.{'resizer_file' if r['tool'] == 'resizer' else 'removebg_file'}",
                batch_id=batch_id, filename=r["processed_filename"]
            ) if exists else None
        })

    return render_template("history.html", items=items)


@history_bp.route("/history/delete/<int:record_id>", methods=["POST"])
@login_required
def delete_one(record_id):
    user = current_user()
    record = db.get_history_record(record_id, user["id"])

    if record:
        folder = _folder_for(record["tool"], user["id"])
        batch_id = record["batch_id"]
        if batch_id:
            file_path = os.path.join(folder, batch_id, record["processed_filename"])
            if os.path.isfile(file_path):
                try:
                    os.remove(file_path)
                except OSError:
                    pass
        db.delete_history_record(record_id, user["id"])
        flash("Image deleted from history.", "success")

    return redirect(url_for("history.history_page"))


@history_bp.route("/history/clear", methods=["POST"])
@login_required
def clear_all():
    user = current_user()
    records = db.get_history_for_user(user["id"])

    for record in records:
        folder = _folder_for(record["tool"], user["id"])
        batch_id = record["batch_id"]
        if batch_id:
            file_path = os.path.join(folder, batch_id, record["processed_filename"])
            if os.path.isfile(file_path):
                try:
                    os.remove(file_path)
                except OSError:
                    pass

    db.clear_history_for_user(user["id"])
    flash("All history cleared.", "success")
    return redirect(url_for("history.history_page"))
