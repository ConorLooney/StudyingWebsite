from flask import request, flash

from study.db import get_db
from study.validation import presence_check, lookup_check

def get_routine(routine_id):
    db = get_db()
    routine = db.execute(
        "SELECT * FROM routine WHERE id = ?",
        (str(routine_id),)
    ).fetchone()
    return routine

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