from flask import request, render_template, g, flash

from study.db import get_db

from .main import bp
from .view_levels import admin_level_view

def read_form():
    return request.form["routine_id"]

"""Returns routines that fit one of
- the user owns the routine AND routine is not already in class"""
def get_routines(class_id):
    db = get_db()

    routines = db.execute(
        "SELECT * FROM routine WHERE owner_id = ?",
        (str(g.user["id"]),)
    ).fetchall()

    routines_in_class = db.execute(
        "SELECT routine_id FROM routine_class WHERE class_id = ?",
        (str(class_id),)
    ).fetchall()
    routines_in_class = [x["routine_id"] for x in routines_in_class]

    routines_not_in_class = []
    for routine in routines:
        if routine["id"] not in routines_in_class:
            routines_not_in_class.append(routine)

    return routines_not_in_class

def save_routine(class_id, routine_id):
    db = get_db()
    try:
        db.execute(
            "INSERT INTO routine_class (routine_id, class_id) VALUES (?, ?)",
            (str(routine_id), str(class_id))
        )
        db.commit()
    except db.IntegrityError:
        error = "Error: routine already saved to class"
        flash(error)

@admin_level_view
@bp.route("/add_routines/<class_id>", methods=("GET", "POST"))
def add_routines(class_id):
    if request.method == "POST":
        routine_id = read_form()
        save_routine(class_id, routine_id)

    routines = get_routines(class_id)

    return render_template("class/add_routines.html", routines=routines)