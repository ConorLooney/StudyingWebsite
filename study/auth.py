import functools
from flask import (
    redirect, url_for, Blueprint, request, render_template, flash, session
)
from werkzeug.security import generate_password_hash, check_password_hash
from study.utility.general import get_user_root_folder
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
                cursor = db.cursor()
                cursor.execute(
                    "INSERT INTO user (username, password) VALUES (?, ?)",
                    (str(username), generate_password_hash(password),)
                )
                user_id = cursor.lastrowid
                db.execute(
                    "INSERT INTO folder (title, owner_id, parent_id) VALUES (?, ?, ?)",
                    ("root", str(user_id), str(-1),)
                )
                db.commit()

                return redirect(url_for("auth.login"))
            except db.IntegrityError:
                error = "Error: Username taken"
        
        flash(error)

    return render_template("auth/register.html")

@bp.route("/login", methods=("GET", "POST"))
def login():
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
                    session["folder_id"] = get_user_root_folder(user["id"])["id"]
                    return redirect(url_for("index"))
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
    g.pop("folder", None)
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
        folder_id = session["folder_id"]
        folder = db.execute(
            "SELECT * FROM folder WHERE id = ?",
            (str(folder_id),)
        ).fetchone()
        g.user = user
        g.folder = folder

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

"""Only allows viewing if the user owns the deck"""
def owner_deck_view(view):
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

"""Only allows viewing if the user owns the deck,
if the user is a member of class that the deck is saved in,
or if the deck is public"""
def member_deck_view(view):
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
        if g.user['id'] == authorised_id:
            return view(**kwargs)
        
        classes = db.execute(
            "SELECT * FROM class \
            JOIN deck_class ON class.id = deck_class.class_id \
            WHERE deck_class.deck_id = ?",
            (str(deck_id),)
        ).fetchall()
        for class_ in classes:
            membership = db.execute(
                "SELECT * FROM user_class \
                WHERE class_id = ? AND user_id = ?",
                (str(class_["id"]), str(g.user["id"]),)
            ).fetchone()
            if membership is not None:
                return view(**kwargs)

        return redirect(url_for("/index"))
    
    return wrapped_view

"""Only allows viewing if the user owns the deck or the deck is public"""
def stranger_deck_view(view):
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

"""Only allows viewing if the user owns the routine"""
def owner_routine_view(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            return redirect(url_for("auth.login"))

        routine_id = kwargs['routine_id']
        db = get_db()
        routine = db.execute(
            "SELECT * FROM routine WHERE id = ?",
            (str(routine_id),)
        ).fetchone()

        if routine is None:
            return redirect(url_for("/index"))

        authorised_id = routine['owner_id']
        if g.user['id'] != authorised_id:
            return redirect(url_for("/index"))

        return view(**kwargs)
    
    return wrapped_view

"""Only allows viewing if the user owns the routine,
if the user is a member of class that the routine is saved in"""
def member_routine_view(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            return redirect(url_for("auth.login"))

        routine_id = kwargs['routine_id']
        db = get_db()
        routine = db.execute(
            "SELECT * FROM routine WHERE id = ?",
            (str(routine_id),)
        ).fetchone()

        if routine is None:
            return redirect(url_for("/index"))

        authorised_id = routine['owner_id']
        if g.user['id'] == authorised_id:
            return view(**kwargs)
        
        classes = db.execute(
            "SELECT * FROM class \
            JOIN routine_class ON class.id = routine_class.class_id \
            WHERE routine_class.routine_id = ?",
            (str(routine_id),)
        ).fetchall()

        for class_ in classes:
            membership = db.execute(
                "SELECT * FROM user_class \
                WHERE class_id = ? AND user_id = ?",
                (str(class_["id"]), str(g.user["id"]),)
            ).fetchone()
            if membership is not None:
                return view(**kwargs)

        return redirect(url_for("index"))
    
    return wrapped_view