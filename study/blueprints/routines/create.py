from flask import request, url_for, render_template, redirect, flash, g
from study.db import get_db
from study.auth import login_required

from .main import bp

class Step:

    def __init__(self, name, abbreviation):
        self.name = name
        self.abbreviation = abbreviation

@bp.route("/create", methods=("GET", "POST"))
@login_required
def create():
    if request.method == "POST":
        routine_name = request.form["routine_name"]
        steps = request.form["steps"]
        mode = request.form["mode"]
        is_step_mode = 1 if mode == "step_mode" else 0

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
                    "INSERT INTO routine (owner_id, title, steps, is_step_mode) VALUES (?, ?, ?, ?)",
                    (str(g.user['id']), routine_name, steps, str(is_step_mode))
                )
                db.commit()
                routine_id = cursor.lastrowid

                return redirect(url_for("routines.view_routine", routine_id=routine_id))
            except db.IntegrityError:
                error = "Routine name must be unique"

        flash(error)

    avaliable_steps = [
        Step("Ask", "a"),
        Step("Correct", "c"),
        Step("Choice", "m"),
        Step("Flashcard", "f"),
        Step("Blanks", "b")
        ]
    
    return render_template("routines/create.html",
    steps=avaliable_steps)