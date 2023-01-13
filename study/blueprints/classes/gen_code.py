from flask import render_template, request, redirect, url_for, flash
from study.auth import login_required
from study.db import get_db
from study.utility.helper import gen_random_code

from .main import bp
from .view_levels import admin_level_view

def get_class_code(class_id):
    db = get_db()
    code = db.execute(
        "SELECT * FROM invite_code WHERE class_id = ?",
        (str(class_id),)
    ).fetchone()
    return code

def make_new_code(class_id, ATTEMPT_LIMIT = 1000):
    """Return and put into database a valid code for the given class
    
    A code is only valid if it is unique, i.e. no other codes in the database
    have the same value. This function attempts to generate a random code,
    if it does not exist, return that. Otherwise it generates another code and
    repeats. It will do this until it reaches the set attempt limit and then
    generate an error and return a rogue value"""
    db = get_db()
    attempt = 0
    while attempt < ATTEMPT_LIMIT:
        try:
            new_code = gen_random_code(length=8)
            db.execute(
                "INSERT INTO invite_code (code, class_id) VALUES (?, ?)",
                (str(new_code), str(class_id),)
            )
            db.commit()
            return new_code
        except db.IntegrityError:
            attempt += 1
            continue
    error = "Error: Could not generate unique code"
    flash(error)
    return -1

def handle_gen_code(code, class_id):
    """Return new code (row record, not value) after request to generate a new code
    
    New code is only generated if given code is None. If the given code is not None,
    i.e. it is already a code, an error is displayed and it is returned."""
    db = get_db()
    if code is not None: # code already exists
        error = "Error: Code is already generated"
        flash(error)
    else:
        new_code = make_new_code(class_id)
        # -1 is rogue value for if a unique code could not be made
        if new_code != -1:
            code = db.execute(
                "SELECT * FROM invite_code WHERE code = ?",
                (str(new_code),)
            ).fetchone()
            return code
    return code

def handle_delete_code(code):
    """Delete given code if it exists. Otherwise display error"""
    db = get_db()
    if code is None:
        error = "Error: No code to delete"
        flash(error)
    else:
        db.execute(
            "DELETE FROM invite_code WHERE code = ?",
            (str(code["code"]),)
        )
        db.commit()
        code = None

@bp.route("/gen_code/<class_id>", methods=("GET", "POST"))
@login_required
@admin_level_view
def gen_code(class_id):
    # displays the current code for the class
    # user can delete that code
    # user can generate a new code
    code = get_class_code(class_id)

    if request.method == "POST":
        if "gen_code" in request.form:
            code = handle_gen_code(code, class_id)
        if "delete_code" in request.form:
            handle_delete_code(code)
            code = None
            
    return render_template("class/gen_code.html", code=code)