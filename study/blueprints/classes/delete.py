from flask import render_template, request, redirect, url_for, g, flash
from werkzeug.security import check_password_hash
from study.auth import login_required
from study.db import get_db
from study.utility.general import delete_class

from .main import bp
from .view_levels import owner_level_view

@bp.route("/delete/<class_id>", methods=("GET", "POST"))
@login_required
@owner_level_view
def delete(class_id):
    db = get_db()
    if request.method == "POST":
        password = request.form["password"]

        error = None

        if password is None:
            error = "Error: Password is required"

        if check_password_hash(g.user["password"], password):
            delete_class(class_id)
            return redirect(url_for("/index"))
        else:
            error = "Incorrect password"

        flash(error)
    
    class_ = db.execute(
        "SELECT * FROM class WHERE id = ?",
        (str(class_id),)
    ).fetchone()

    return render_template("class/delete.html", class_=class_)