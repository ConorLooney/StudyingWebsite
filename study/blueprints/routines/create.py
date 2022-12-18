from flask import request, url_for, render_template, redirect, flash, g
from study.db import get_db
from study.auth import login_required

from .main import bp
from .utility import read_form, validate
from study.blueprints.learn.steps import get_all_steps

class Step:

    def __init__(self, name, abbreviation):
        self.name = name
        self.abbreviation = abbreviation

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
    
    return render_template("routines/create.html",
    steps=get_all_steps())