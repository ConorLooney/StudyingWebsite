from flask import request, url_for, render_template, redirect, flash
from study.db import get_db
from study.auth import login_required, owner_routine_view

from .main import bp

@bp.route("/update/<routine_id>", methods=("GET", "POST"))
@login_required
@owner_routine_view
def update(routine_id):
    db = get_db()

    if request.method == "POST":
        routine_name = request.form["routine_name"]
        steps = request.form["steps"]

        error = None
        if routine_name is None:
            error = "Routine name is required"
        if steps is None:
            error = "Routine steps are required"

        if error is None:
            try:

                db.execute(
                    "UPDATE routine SET title = ?, steps = ?, WHERE id = ?",
                    (routine_name, steps, str(routine_id),)
                )
                db.commit()

                return redirect(url_for("routines.view_routine", routine_id=routine_id))
            except db.IntegrityError:
                error = "Routine name must be unique"

        flash(error) 

    current_routine = db.execute(
        "SELECT * FROM routine WHERE id = ?",
        (str(routine_id),)
    ).fetchone()

    return render_template("routines/update.html", routine=current_routine)