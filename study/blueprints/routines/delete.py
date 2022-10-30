from flask import request, url_for, render_template, redirect, flash, g
from werkzeug.security import check_password_hash
from study.db import get_db
from study.auth import login_required, owner_routine_view

from .main import bp

@bp.route("/delete/<routine_id>", methods=("GET", "POST"))
@login_required
@owner_routine_view
def delete(routine_id):
    db = get_db()
    if request.method == "POST":
        password = request.form["password"]
        
        error = None

        if password is None:
            error = "Password is required"
        
        if error is None:
            if check_password_hash(g.user["password"], password):
                db.execute(
                    "DELETE FROM routine WHERE id = ?",
                    (str(routine_id),)
                )
                db.commit()
                return redirect(url_for("routines.all_user"))
            else:
                error = "Incorrect password"
        
        flash(error)

    routine = db.execute(
        "SELECT * FROM routine WHERE id = ?",
        (str(routine_id),)
    ).fetchone()

    return render_template("routines/delete.html", routine=routine)