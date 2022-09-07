import functools
from flask import (
    Blueprint, render_template, request, redirect, url_for, g, flash
)
from werkzeug.security import check_password_hash
from study.auth import login_required
from study.db import get_db, to_bit

bp = Blueprint("class", __name__, url_prefix="/class")

def protected_class_view(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            return redirect(url_for("auth.login"))

        class_id = kwargs['class_id']
        db = get_db()
        current_class = db.execute(
            "SELECT * FROM class WHERE id = ?",
            (str(class_id),)
        ).fetchone()

        if current_class is None:
            return redirect(url_for("/index"))

        authorised_ids = [current_class['owner_id']]
        authorised_ids.extend(db.execute(
            "SELECT user_id FROM user_class WHERE class_id = ?",
            (str(class_id),)
        ).fetchall())
        if g.user['id'] not in authorised_ids:
            return redirect(url_for("/index"))

        return view(**kwargs)
    
    return wrapped_view

def private_class_view(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            return redirect(url_for("auth.login"))

        class_id = kwargs['class_id']
        db = get_db()
        current_class = db.execute(
            "SELECT * FROM class WHERE id = ?",
            (str(class_id),)
        ).fetchone()

        if current_class is None:
            return redirect(url_for("/index"))

        if g.user['id'] == current_class["owner_id"]:
            return view(**kwargs)
        else:
            return redirect(url_for("/index"))
    
    return wrapped_view

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
            cursor.execute(
                "INSERT INTO user_class (user_id, class_id) VALUES (?, ?)",
                (str(g.user["id"]), str(class_id),)
            )
            db.commit()

            return redirect(url_for("class.view", class_id=class_id))

        flash(error)
    return render_template("class/create.html")

@bp.route("/view/<class_id>")
@login_required
@protected_class_view
def view(class_id):
    db = get_db()

    view_class = db.execute(
        "SELECT * FROM class WHERE id = ?",
        (str(class_id),)
    ).fetchone()

    members = db.execute(
        "SELECT * FROM user\
        JOIN user_class ON user_id\
        WHERE class_id = ?",
        (str(class_id),)
    ).fetchall()
    
    return render_template("class/view.html", view_class=view_class, members=members)

@bp.route("/all_user", methods=("GET", "POST"))
@login_required
def all_user():
    if request.method == "POST":
        if "update_class" in request.form:
            class_id = request.form["class_id"]
            return redirect(url_for("class.update", class_id=class_id))
        if "delete_class" in request.form:
            class_id = request.form["class_id"]
            return redirect(url_for("class.delete", class_id=class_id))

    db = get_db()
    
    classes = db.execute(
        "SELECT * FROM class \
        JOIN user_class ON class.id = user_class.class_id \
        WHERE user_class.user_id = ?",
        (str(g.user["id"]),)
    ).fetchall()

    owned_info = []
    for class_ in classes:
        owned = db.execute(
            "SELECT * FROM class WHERE owner_id = ? AND id = ?",
            (str(g.user["id"]), str(class_["id"]),)
        ).fetchall()
        if len(owned) > 0:
            owned_info.append(True)
        else:
            owned_info.append(False)

    return render_template("class/all_user.html", classes=classes, owned_info=owned_info)

@bp.route("/all_public", methods=("GET", "POST"))
@login_required
def all_public():
    db = get_db()
    classes = db.execute(
        "SELECT * FROM class WHERE is_public = ?",
        (str(to_bit(True)),)
    ).fetchall()

    member_info = []
    for class_ in classes:
        if str(class_["owner_id"]) == str(g.user["id"]):
            member_info.append(1)
            continue

        membership = db.execute(
            "SELECT * FROM user_class \
            WHERE user_class.user_id = ? AND user_class.class_id = ?",
            (str(g.user["id"]), str(class_["id"]),)
        ).fetchone()

        if membership is None:
            member_info.append(-1)
        else:
            member_info.append(0)

    print(member_info)

    return render_template("class/all_public.html", classes=classes, member_info=member_info)

@bp.route("/update/<class_id>", methods=("GET", "POST"))
@login_required
@private_class_view
def update(class_id):
    db = get_db()
    if request.method == "POST":
        title = request.form["title"]
        description = request.form["description"]
        is_public = request.form["is_public"] == "public"
        db.execute(
            "UPDATE class SET title = ?, description = ?, is_public = ? \
            WHERE id = ?",
            (str(title), str(description), str(to_bit(is_public)), str(class_id),)
        )
        db.commit()
        return redirect(url_for("class.view", class_id=class_id))

    class_ = db.execute(
        "SELECT * FROM class WHERE id = ?",
        (str(class_id),)
    ).fetchone()
    return render_template("class/update.html", class_=class_)

@bp.route("/delete/<class_id>", methods=("GET", "POST"))
@login_required
@private_class_view
def delete(class_id):
    db = get_db()
    if request.method == "POST":
        password = request.form["password"]

        error = None

        if password is None:
            error = "Error: Password is required"

        if check_password_hash(g.user["password"], password):
            db.execute(
                "DELETE FROM class WHERE id = ?",
                (str(class_id),)
            )
            db.commit()
            db.execute(
                "DELETE FROM user_class WHERE class_id = ?",
                (str(class_id))
            )
            db.commit()
            return redirect(url_for("/index"))
        else:
            error = "Incorrect password"

        flash(error)
    
    class_ = db.execute(
        "SELECT * FROM class WHERE id = ?",
        (str(class_id),)
    ).fetchone()
    return render_template("class/delete.html", class_=class_)