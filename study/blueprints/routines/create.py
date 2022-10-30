from flask import request, url_for, render_template, redirect, flash, g
from study.db import get_db, to_bit
from study.auth import login_required

from .main import bp

@bp.route("/create", methods=("GET", "POST"))
@login_required
def create():
    if request.method == "POST":
        routine_name = request.form["routine_name"]
        steps = request.form["steps"]
        is_public = request.form["is_public"] == "1"

        error = None
        if routine_name is None:
            error = "Routine name is required"
        if steps is None:
            error = "Routine steps are required"

        if error is None:
            db = get_db()
            cursor = db.cursor()
            try:

                cursor.execute(
                    "INSERT INTO routine (owner_id, title, steps, is_public) VALUES (?, ?, ?, ?)",
                    (str(g.user['id']), routine_name, steps, to_bit(is_public),)
                )
                db.commit()
                routine_id = cursor.lastrowid

                return redirect(url_for("routines.view_routine", routine_id=routine_id))
            except db.IntegrityError:
                error = "Routine name must be unique"

        flash(error) 
    
    return render_template("routines/create.html")