from flask import render_template, request, redirect, url_for, g, flash
from study.auth import login_required
from study.db import get_db, to_bit

from .main import bp

"""Page for user to create a new class

User must be logged in
Takes class name, description and is public or private


Inserts new class row in class table
Inserts new mebership in user_class table"""
@bp.route("/create", methods=("GET", "POST"))
@login_required
def create():
    if request.method == "POST":
        title = request.form["title"]
        description = request.form["description"]
        is_public = request.form["is_public"] == "public"

        error = None

        if title is None:
            error = "Error: Class name is required"

        if error is None:
            db = get_db()
            cursor = db.cursor()
            cursor.execute(
                "INSERT INTO class (owner_id, title, description, is_public) VALUES (?, ?, ?, ?)",
                (str(g.user["id"]), str(title), str(description), to_bit(is_public),)
            )
            db.commit()
            class_id = cursor.lastrowid
            cursor = db.cursor()
            try:
                cursor.execute(
                    "INSERT INTO user_class (user_id, class_id) VALUES (?, ?)",
                    (str(g.user["id"]), str(class_id),)
                )
                db.commit()
                return redirect(url_for("class.view", class_id=class_id))
            except db.IntegrityError:
                error = "Error: User already member of this class"


        flash(error)
    return render_template("class/create.html")