from flask import request, url_for, render_template, redirect, flash, g
from werkzeug.security import check_password_hash
from study.db import get_db
from study.auth import login_required, owner_routine_view

from .main import bp
from .utility import get_routine
from study.validation import presence_check

def delete_routine_from_db(routine_id):
    db = get_db()
    db.execute(
        "DELETE FROM routine WHERE id = ?",
        (str(routine_id),)
    )
    db.commit()

@bp.route("/delete/<routine_id>", methods=("GET", "POST"))
@login_required
@owner_routine_view
def delete(routine_id):
    if request.method == "POST":
        password = request.form["password"]

        if not presence_check(password):
            flash("Error: No password entered")
        else:
            if check_password_hash(g.user["password"], password):
                delete_routine_from_db(routine_id)
                return redirect(url_for("routines.see_all"))
            else:
               flash("Error: Incorrect password entered")

    routine = get_routine(routine_id)

    return render_template("routines/delete.html", routine=routine)