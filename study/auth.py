import functools
from flask import (
    redirect, url_for, Blueprint, request, render_template, flash, session
)
from werkzeug.security import generate_password_hash, check_password_hash
from study.db import get_db, to_bool, g

bp = Blueprint("auth", __name__, url_prefix="/auth")

@bp.route("/register", methods=("GET", "POST"))
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        retyped_password = request.form["retyped_password"]

        error = None

        if username is None:
            error = "Error: Username is required"
        if password is None:
            error = "Error: Password is required"
        if retyped_password is None:
            error = "Error: Password confirmation is required"
        if password != retyped_password:
            error = "Error: Passwords do not match"
        
        if error is None:
            try:
                db = get_db()
                db.execute(
                    "INSERT INTO user (username, password) VALUES (?, ?)",
                    (str(username), generate_password_hash(password),)
                )
                db.commit()

                return redirect(url_for("auth.login"))
            except db.IntegrityError:
                error = "Error: Username taken"
        
        flash(error)

    return render_template("auth/register.html")

@bp.route("/login", methods=("GET", "POST"))
def login():
    print(request.method)
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        error = None

        if username is None:
            error = "Error: Username is required"
        if password is None:
            error = "Error: Password is required"
        
        if error is None:
            db = get_db()
            users = db.execute(
                "SELECT * FROM user WHERE username = ?",
                (str(username),)
            ).fetchall()

            if len(users) == 1:
                user = users[0]
                if check_password_hash(user["password"], password):
                    session["user_id"] = user["id"]
                    return redirect(url_for("/index"))
                else:
                    error = "Error: Incorrect password"
            else:
                error = "Error: Invalid username"

        flash(error)

    return render_template("auth/login.html")

@bp.route("/logout")
def logout():
    session.clear()
    g.pop("user", None)
    return redirect(url_for("auth.login"))

@bp.before_app_request
def load_logged_in_user():
    if "user_id" in session:
        db = get_db()
        user_id = session["user_id"]
        user = db.execute(
            "SELECT * FROM user WHERE id = ?",
            (str(user_id),)
        ).fetchone()
        g.user = user

def login_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if session.get("user_id") is None:
            return redirect(url_for("auth.register"))
        else:
            db = get_db()
            user_id = session["user_id"]
            user = db.execute(
                "SELECT * FROM user WHERE id = ?",
                (str(user_id),)
            ).fetchall()[0]
            g.user = user

        return view(**kwargs)
    
    return wrapped_view

"""Will only allow viewing of the passed in view if the user is the owner
of the deck or the deck is public"""
def protected_deck_view(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            return redirect(url_for("auth.login"))

        deck_id = kwargs['deck_id']
        db = get_db()
        deck = db.execute(
            "SELECT * FROM deck WHERE id = ?",
            (str(deck_id),)
        ).fetchone()

        if deck is None:
            return redirect(url_for("/index"))
        
        if to_bool(deck["is_public"]):
            return view(**kwargs)

        authorised_id = deck['owner_id']
        if g.user['id'] != authorised_id:
            return redirect(url_for("/index"))

        return view(**kwargs)
    
    return wrapped_view

"""Will only allow viewing of the passed in view if the user is the owner
of the deck"""
def private_deck_view(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            return redirect(url_for("auth.login"))

        deck_id = kwargs['deck_id']
        db = get_db()
        deck = db.execute(
            "SELECT * FROM deck WHERE id = ?",
            (str(deck_id),)
        ).fetchone()

        if deck is None:
            return redirect(url_for("/index"))

        authorised_id = deck['owner_id']
        if g.user['id'] != authorised_id:
            return redirect(url_for("/index"))

        return view(**kwargs)
    
    return wrapped_view

"""Will only allow viewing of the passed in view if the user is the owner
of the routine or the routine is public"""
def protected_routine_view(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            return redirect(url_for("auth.login"))

        routine_id = kwargs["routine_id"]
        db = get_db()
        routine = db.execute(
            "SELECT * FROM routine WHERE id = ?",
            (str(routine_id),)
        ).fetchone()

        if routine is None:
            return redirect(url_for("/index"))
        
        if to_bool(routine["is_public"]):
            return view(**kwargs)

        authorised_id = routine['owner_id']
        if g.user['id'] != authorised_id:
            return redirect(url_for("/index"))

        return view(**kwargs)

    return wrapped_view

"""Will only allow viewing of the passed in view if the user is the owner
of the routine"""
def private_routine_view(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            return redirect(url_for("auth.login"))

        routine_id = kwargs["routine_id"]
        db = get_db()
        routine = db.execute(
            "SELECT * FROM routine WHERE id = ?",
            (str(routine_id),)
        ).fetchone()

        if routine is None:
            return redirect(url_for("/index"))

        authorised_id = routine["owner_id"]
        if g.user['id'] != authorised_id:
            return redirect(url_for("/index"))

        return view(**kwargs)
    
    return wrapped_view
