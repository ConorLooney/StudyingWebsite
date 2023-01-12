from flask import render_template, request, redirect, url_for, g
from study.auth import login_required
from study.db import get_db

from .main import bp
from .utility import validate_data, new_class_member_in_database

def read_form():
    return [
        request.form["title"],
        request.form["description"],
        request.form["is_public"]
    ]

def new_class_in_database(title, description, is_public):
    """Creates a new class in the database with the given values at attributes
    and the owner id as the id of the user currently logged in and returns the 
    id of the new class"""
    db = get_db()
    cursor = db.cursor()
    cursor.execute(
        "INSERT INTO class (owner_id, title, description, is_public) VALUES (?, ?, ?, ?)",
        (str(g.user["id"]), str(title), str(description), int(is_public),)
    )
    db.commit()
    return cursor.lastrowid

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