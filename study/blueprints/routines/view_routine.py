from flask import render_template, request
from study.db import get_db
from study.auth import login_required, member_routine_view

from .main import bp

"""Return routine with corresponding id"""
def get_routine(routine_id):
    db = get_db()
    routine = db.execute(
        "SELECT * FROM routine WHERE id = ?",
        (str(routine_id),)
    ).fetchone()
    return routine

@bp.route("/view/<routine_id>")
@login_required
@member_routine_view
def view_routine(routine_id):
    routine = get_routine(routine_id)

    return render_template("routines/routine.html", routine=routine)