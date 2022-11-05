from flask import render_template, request, redirect, url_for
from study.auth import login_required
from study.db import get_db, to_bit

from .main import bp
from .view_levels import owner_level_view
from .utility import validate_data

def get_class(class_id):
    db = get_db()
    return db.execute(
        "SELECT * FROM class WHERE id = ?",
        (str(class_id),)
    ).fetchone()

def read_form():
    return [
        request.form["title"],
        request.form["description"],
        request.form["is_public"]
    ]

def update_class_in_database(class_id, title, description, is_public):
    """Updates class data with given attributes"""
    db = get_db()
    db.execute(
        "UPDATE class SET title = ?, description = ?, is_public = ? \
        WHERE id = ?",
        (str(title), str(description), str(to_bit(is_public)), str(class_id),)
    )
    db.commit()

@bp.route("/update/<class_id>", methods=("GET", "POST"))
@login_required
@owner_level_view
def update(class_id):
    if request.method == "POST":
        title, description, is_public = read_form()
        is_public = is_public == "public"
        if validate_data(title, description, is_public):
            update_class_in_database(class_id, title, description, is_public)
        return redirect(url_for("class.view", class_id=class_id))
        
    return render_template("class/update.html", display_class=get_class(class_id))