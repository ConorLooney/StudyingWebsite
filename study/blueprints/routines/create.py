from flask import request, url_for, render_template, redirect, flash, g
from study.db import get_db
from study.auth import login_required

from .main import bp
from study.validation import presence_check, lookup_check

class Step:

    def __init__(self, name, abbreviation):
        self.name = name
        self.abbreviation = abbreviation

def read_form():
    """Returns the form data formatted"""
    name = request.form["routine_name"]
    steps = request.form["steps"]
    mode = request.form["mode"]
    is_step_mode = 1 if mode == "step_mode" else 0
    return name, steps, is_step_mode

def validate(name, steps, is_step_mode):
    """Returns false if any of the data is invalid
    
    Also displays an error if the data is invalid"""
    if not presence_check(name):
        flash("Error: Invalid routine name")
        return False
    
    if not presence_check(steps):
        flash("Error: Invalid routine steps")
        return False
    
    if not lookup_check(is_step_mode, [0, 1]):
        flash("Error: Invalid step or term mode")
        return False
    
    return True

def insert_routine_in_db(name, steps, is_step_mode):
    db = get_db()
    cursor = db.cursor()
    cursor.execute(
        "INSERT INTO routine (owner_id, title, steps, is_step_mode) VALUES (?, ?, ?, ?)",
        (str(g.user["id"]), name, steps, str(is_step_mode),)
    )
    db.commit()
    routine_id = cursor.lastrowid
    return routine_id

@bp.route("/create", methods=("GET", "POST"))
@login_required
def create():
    if request.method == "POST":
        name, steps, is_step_mode = read_form()
        if validate(name, steps, is_step_mode):
            routine_id = insert_routine_in_db(name, steps, is_step_mode)
            return redirect(url_for("routines.see_one", routine_id=routine_id))

    avaliable_steps = [
        Step("Ask", "a"),
        Step("Correct", "c"),
        Step("Choice", "m"),
        Step("Flashcard", "f"),
        Step("Blanks", "b")
        ]
    
    return render_template("routines/create.html",
    steps=avaliable_steps)