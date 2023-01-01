from flask import render_template, g

from study.auth import login_required
from study.db import get_db
from .main import bp

def get_user_spaced_repetition_settings():
    user_id = g.user["id"]
    db = get_db()

    spaced_repetition_settings = db.execute(
        "SELECT * FROM spaced_repetition_setting WHERE user_id = ?",
        (str(user_id),)
    ).fetchall()

    return spaced_repetition_settings

@bp.route("/list")
def list():
    spaced_repetition_settings = get_user_spaced_repetition_settings()
    return render_template("spaced_repetition/list.html",
    spaced_repetition_settings=spaced_repetition_settings)