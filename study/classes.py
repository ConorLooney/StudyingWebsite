import functools
from flask import (
    Blueprint, render_template, request, redirect, url_for, g, flash
)
from study.auth import login_required
from study.db import get_db, to_bool, to_bit

bp = Blueprint("class", __name__, url_prefix="/class")

def protected_class_view(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            return redirect(url_for("auth.login"))

        class_id = kwargs['class_id']
        db = get_db()
        current_class = db.execute(
            "SELECT * FROM class WHERE id = ?",
            (str(class_id),)
        ).fetchone()

        if current_class is None:
            return redirect(url_for("/index"))
        
        if to_bool(current_class["is_public"]):
            return view(**kwargs)

        authorised_ids = [current_class['owner_id']]
        authorised_ids.extend(db.execute(
            "SELECT user_id FROM class_member WHERE class_id = ?",
            (str(class_id))
        ).fetchall())
        if g.user['id'] not in authorised_ids:
            return redirect(url_for("/index"))

        return view(**kwargs)
    
    return wrapped_view

@bp.route("/create", methods=("GET", "POST"))
@login_required
def create():
    if request.method == "POST":
        title = request.form["title"]
        is_public = request.form["is_public"] == "public"

        error = None

        if title is None:
            error = "Error: Class name is required"

        if error is None:
            db = get_db()
            cursor = db.cursor()
            cursor.execute(
                "INSERT INTO class (owner_id, title, is_public) VALUES (?, ?, ?)",
                (str(g.user["id"]), str(title), to_bit(is_public),)
            )
            db.commit()
            class_id = cursor.lastrowid

            return redirect(url_for("class.view", class_id=class_id))

        flash(error)
    return render_template("class/create.html")

@bp.route("/view/<class_id>")
@login_required
@protected_class_view
def view(class_id):
    db = get_db()

    view_class = db.execute(
        "SELECT * FROM class WHERE id = ?",
        (str(class_id),)
    ).fetchone()

    members = db.execute(
        "SELECT * FROM user\
        JOIN user_class ON user_id\
        WHERE class_id = ?",
        (str(class_id),)
    ).fetchall()
    
    return render_template("class/view.html", view_class=view_class, members=members)

@bp.route("/all_user", methods=("GET", "POST"))
@login_required
def all_user():
    return render_template("class/all_user.html", classes=classes, owned_info=owned_info)