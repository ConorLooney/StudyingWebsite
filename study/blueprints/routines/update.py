from flask import request, url_for, render_template, redirect, flash
from study.db import get_db
from study.auth import login_required, owner_routine_view

from .main import bp
from .utility import get_routine, read_form, validate

class Step:

    def __init__(self, name, abbreviation):
        self.name = name
        self.abbreviation = abbreviation

def update_routine_in_db(routine_id, name, steps, is_step_mode):
    db = get_db()
    db.execute(
        "UPDATE routine SET title = ?, steps = ?, is_step_mode = ? WHERE id = ?",
        (name, steps, str(is_step_mode), str(routine_id),)
    )
    db.commit()

@bp.route("/update/<routine_id>", methods=("GET", "POST"))
@login_required
@owner_routine_view
def update(routine_id):
    if request.method == "POST":
        name, steps, is_step_mode = read_form()

        if validate(name, steps, is_step_mode):
            update_routine_in_db(routine_id, name, steps, is_step_mode)
            return redirect(url_for("routines.see_one", routine_id=routine_id))

    routine = get_routine(routine_id)

    avaliable_steps = [
        Step("Ask", "a"),
        Step("Correct", "c"),
        Step("Choice", "m"),
        Step("Flashcard", "f"),
        Step("Blanks", "b"),
        Step("Copy", "y")
        ]

    return render_template("routines/update.html", routine=routine,
    steps=avaliable_steps)