from flask import render_template
from study.db import get_db
from study.auth import login_required, member_routine_view

from .main import bp

@bp.route("/view/<routine_id>")
@login_required
@member_routine_view
def view_routine(routine_id):
    db = get_db()
    routine = db.execute(
        "SELECT * FROM routine WHERE id = ?",
        (str(routine_id),)
    ).fetchone()

    return render_template("routines/routine.html", routine=routine)