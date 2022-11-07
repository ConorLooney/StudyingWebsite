from flask import render_template, request, redirect, url_for, g, flash
from study.auth import login_required
from study.db import get_db
from study.utility.general import add_user_to_class
import time

from study.validation import presence_check
from .main import bp

def validate_code(code):
    """Return true if the given code is valid false otherwise
    
    Checks if the code is valid data (not if it is verified as a real code)"""
    if not presence_check(code):
        error = "Error: No code entered"
        flash(error)
        return False
    return True

def get_code(code):
    db = get_db()
    invite_code = db.execute(
        "SELECT * FROM invite_code WHERE code = ?",
        (str(code),)
    ).fetchone()
    if invite_code is None:
        error = "Error: Incorrect code"
        flash(error)
        return False
    return invite_code

def get_code_age(code):
    db = get_db()
    time_created = int(db.execute(
        "SELECT unixepoch(created) FROM invite_code WHERE \
        id = ?",
        (str(code["id"]),)
    ).fetchone()["unixepoch(created)"])
    age = time.time() - time_created
    return age

def verify_code(code, INVITE_CODE_LIFETIME=30*60):
    """Return true if the code is not expired false otherwise
    
    Default code lifetime of half an hour (30 minutes of 60 seconds)"""

    code_age = get_code_age(code)
    if code_age > INVITE_CODE_LIFETIME:
        error = "Error: Code has expired"
        flash(error)
        return False
    return True

def delete_code(code):
    db = get_db()
    db.execute(
        "DELETE FROM invite_code WHERE id = ?",
        (str(code["id"]),)
    )
    db.commit()

def process_code_join():
    """Processes the submission of the form to enter a code and attempt to join a class
    Return true if successful (i.e. data valid and user now in class), false otherwise"""
    code = request.form["code"]
    if not validate_code(code):
        return False

    code = get_code(code)
    # get_code returns false if not a code
    if not code:
        return False

    # verifies code by checking it is not expired
    if not verify_code(code):
        delete_code(code)
        return False
    # code is real and not expired

    class_id = code["class_id"]
    # returns false if there is an error, e.g. user is already in class
    if not add_user_to_class(g.user["id"], class_id):
        return False

    return class_id

@bp.route("/code_join", methods=("GET", "POST"))
@login_required
def code_join():
    
    if request.method == "POST":
        class_id = process_code_join()
        if class_id:
            return redirect(url_for("class.view", class_id=class_id))

    return render_template("class/code_join.html")