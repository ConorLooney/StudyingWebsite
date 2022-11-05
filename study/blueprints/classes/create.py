from flask import render_template, request, redirect, url_for, g, flash
from study.auth import login_required
from study.db import get_db, to_bit

from .main import bp
from study.validation import presence_check

def read_form():
    return [
        request.form["title"],
        request.form["description"],
        request.form["is_public"]
    ]

def validate_data(title, description, is_public):
    if not presence_check(title):
        error = "Error: Name for class is required"
        flash(error)
        return False
    
    if not presence_check(description):
        error = "Error: Description of class is required"
        flash(error)
        return False

    if not presence_check(is_public):
        error = "Error: Whether class is public or not is required"
        flash(error)
        return False

    return True

def new_class_in_database(title, description, is_public):
    """Creates a new class in the database with the given values at attributes
    and the owner id as the id of the user currently logged in and returns the 
    id of the new class"""
    db = get_db()
    cursor = db.cursor()
    cursor.execute(
        "INSERT INTO class (owner_id, title, description, is_public) VALUES (?, ?, ?, ?)",
        (str(g.user["id"]), str(title), str(description), to_bit(is_public),)
    )
    db.commit()
    return cursor.lastrowid

def new_class_member_in_database(class_id, user_id):
    """Creates a new record of the class membership and returns false if the
    user is already in this class (and displays this error) otherwise returns true"""
    db = get_db()
    try:
        db.execute(
            "INSERT INTO user_class (user_id, class_id) VALUES (?, ?)",
            (str(user_id), str(class_id),)
        )
        db.commit()
    except db.IntegrityError:
        error = "Error: User already a member of the class"
        flash(error)
        return False
    return True

@bp.route("/create", methods=("GET", "POST"))
@login_required
def create():
    if request.method == "POST":
        title, description, is_public = read_form()
        is_public = is_public == "public"

        if validate_data(title, description, is_public):
            class_id = new_class_in_database(title, description, is_public)
            new_class_member_in_database(class_id, g.user["id"])
            return redirect(url_for("class.view", class_id=class_id))

    return render_template("class/create.html")