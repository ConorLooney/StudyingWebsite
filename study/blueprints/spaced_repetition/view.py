from flask import render_template, g

from study.db import get_db
from .main import bp

def get_spaced_repetition_setting(deck_id, routine_id):
    db = get_db()
    user_id = g.user["id"]
    spaced_repetition_setting = db.execute(
        "SELECT * FROM spaced_repetition_setting WHERE \
        user_id = ? AND deck_id = ? AND routine_id = ?",
        (str(user_id), str(deck_id), str(routine_id),)
    ).fetchone()
    return spaced_repetition_setting

@bp.route("/view/<deck_id>/<routine_id>")
def view(deck_id, routine_id):
    spaced_repetition_setting = get_spaced_repetition_setting(deck_id, routine_id)
    return render_template("spaced_repetition/view.html",
    spaced_repetition_setting=spaced_repetition_setting)