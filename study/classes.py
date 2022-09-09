import functools
from flask import (
    Blueprint, render_template, request, redirect, url_for, g, flash
)
from werkzeug.security import check_password_hash
from study.auth import login_required
from study.db import get_db, to_bit
from study.utility import gen_random_code
import time

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
        authorised_ids.extend([row["user_id"] for row in db.execute(
            "SELECT user_id FROM user_class WHERE class_id = ?",
            (str(class_id),)
        ).fetchall()])
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

@bp.route("/view/<class_id>", methods=("GET", "POST"))
@login_required
@protected_class_view
def view(class_id):
    db = get_db()
    if request.method == "POST":
        error = None

        if "gen_code" in request.form:
            return redirect(url_for("class.gen_code", class_id=class_id))

        if "remove_user" in request.form:
            user_id = request.form["user_id"]
            db.execute(
                "DELETE FROM user_class WHERE user_id = ?",
                (str(user_id),)
            )
            db.execute(
                "DELETE FROM admin_class WHERE admin_id = ?",
                (str(user_id),)
            )
            db.commit()

        if "make_admin" in request.form:
            try:
                user_id = request.form["user_id"]
                db.execute(
                    "INSERT INTO admin_class (admin_id, class_id) VALUES (?, ?)",
                    (str(user_id), str(class_id),)
                )
                db.commit()
            except db.IntegrityError:
                error = "Error: User is already admin of this class"

        if "remove_admin" in request.form:
            user_id = request.form["user_id"]
            db.execute(
                "DELETE FROM admin_class WHERE admin_id = ?",
                (str(user_id),)
            )
            db.commit()

        if "reject_request" in request.form:
            user_id = request.form["user_id"]
            db.execute(
                "DELETE FROM join_request WHERE requester_id = ? AND class_id = ?",
                (str(user_id), str(class_id),)
            )
            db.commit()

        if "accept_request" in request.form:
            user_id = request.form["user_id"]
            try:
                db.execute(
                    "INSERT INTO user_class (user_id, class_id) VALUES (?, ?)",
                    (str(user_id), str(class_id),)
                )
                db.commit()
            except db.IntegrityError:
                error = "Error: User already member of this class"
            db.execute(
                "DELETE FROM join_request WHERE requester_id = ? AND class_id = ?",
                (str(user_id), str(class_id),)
            )
            db.commit()
        
        flash(error)

    view_class = db.execute(
        "SELECT * FROM class WHERE id = ?",
        (str(class_id),)
    ).fetchone()

    members = db.execute(
        "SELECT * FROM user\
        JOIN user_class ON user.id=user_class.user_id\
        WHERE class_id = ?",
        (str(class_id),)
    ).fetchall()

    admins = db.execute(
        "SELECT * FROM user\
        JOIN admin_class ON user.id=admin_class.admin_id\
        WHERE class_id = ?",
        (str(class_id),)
    ).fetchall()

    owner = db.execute(
        "SELECT * FROM user WHERE id = ?",
        (str(view_class["owner_id"]),)
    ).fetchone()

    join_requests = db.execute(
        "SELECT * FROM user\
        JOIN join_request ON user.id=join_request.requester_id\
        WHERE class_id = ?",
        (str(class_id),)
    ).fetchall()

    user = g.user

    is_owner = str(owner["id"]) == str(g.user["id"])
    is_admin = is_owner or str(g.user["id"]) in [str(x["id"]) for x in admins]
    
    return render_template("class/view.html",
     user=user, view_class=view_class, owner=owner, members=members,
      admins=admins, is_owner=is_owner, is_admin=is_admin, join_requests=join_requests)

@bp.route("/all_user", methods=("GET", "POST"))
@login_required
def all_user():
    db = get_db()
    if request.method == "POST":
        if "update_class" in request.form:
            class_id = request.form["class_id"]
            return redirect(url_for("class.update", class_id=class_id))
        if "delete_class" in request.form:
            class_id = request.form["class_id"]
            return redirect(url_for("class.delete", class_id=class_id))
        if "leave_class" in request.form:
            class_id = request.form["class_id"]
            db.execute(
                "DELETE FROM user_class WHERE user_id = ?",
                (str(g.user["id"]),)
            )
            db.execute(
                "DELETE FROM admin_class WHERE admin_id = ?",
                (str(g.user["id"]),)
            )
            db.commit()
    
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
    if request.method == "POST":
        if "code_join_class" in request.form:
            return redirect(url_for("class.code_join"))
        if "request_to_join_class" in request.form:
            class_id = request.form["class_id"]
            try:
                db.execute(
                    "INSERT INTO join_request (requester_id, class_id) VALUES (?, ?)",
                    (str(g.user["id"]), str(class_id),)
                )
                db.commit()
            except db.IntegrityError:
                error = "Error: User has already a request to join this class"
        if "leave_class" in request.form:
            class_id = request.form["class_id"]
            db.execute(
                "DELETE FROM user_class WHERE user_id = ?",
                (str(g.user["id"]),)
            )
            db.execute(
                "DELETE FROM admin_class WHERE admin_id = ?",
                (str(g.user["id"]),)
            )
            db.commit()
        if "delete_class" in request.form:
            class_id = request.form["class_id"]
            return redirect(url_for("class.delete", class_id=class_id))
        
        flash(error)
        
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

@bp.route("/gen_code/<class_id>", methods=("GET", "POST"))
@login_required
@private_class_view
def gen_code(class_id):
    db = get_db()
    code = db.execute(
        "SELECT * FROM invite_code WHERE class_id = ?",
        (str(class_id),)
    ).fetchone()

    if request.method == "POST":
        if "gen_code" in request.form:
            if code is not None:
                error = "Error: Code is already generated"
                flash(error)
                return redirect(url_for("class.gen_code", class_id=class_id))
            else:
                def make_new_code():
                    try:
                        new_code = gen_random_code(length=8)
                        db.execute(
                                "INSERT INTO invite_code (code, class_id) VALUES (?, ?)",
                                (str(new_code), str(class_id),)
                            )
                        db.commit()
                        return new_code
                    except db.IntegrityError:
                        make_new_code()
                new_code = make_new_code()
                code = db.execute(
                    "SELECT * FROM invite_code WHERE code = ?",
                    (str(new_code),)
                ).fetchone()
        if "delete_code" in request.form:
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

    return render_template("class/gen_code.html", code=code)

@bp.route("/code_join", methods=("GET", "POST"))
@login_required
def code_join():
    # in seconds, half an hour
    INVITE_CODE_LIFETIME = 60 * 30
    if request.method == "POST":
        code = request.form["code"]

        error = None

        if code is None:
            error = "Error: Must enter code"

        db = get_db()
        invite_code = db.execute(
            "SELECT * FROM invite_code WHERE code = ?",
            (str(code),)
        ).fetchone()

        if invite_code is None:
            error = "Error: Invalid code"

        if error is None:
            time_since_creation = time.time() - int(db.execute(
                "SELECT unixepoch(created) FROM invite_code WHERE \
                id = ?",
                (str(invite_code["id"]),)
            ).fetchone()["unixepoch(created)"])
            
            if time_since_creation > INVITE_CODE_LIFETIME:
                db.execute(
                    "DELETE FROM invite_code WHERE id = ?",
                    (str(invite_code["id"]),)
                )
                db.commit()
                error = "Error: Code has expired"

        if error is None:
            class_id = invite_code["class_id"]

            members = [row["user_id"] for row in db.execute(
                "SELECT user_id FROM user_class WHERE class_id = ?",
                (str(class_id),)
            ).fetchall()]
            if g.user["id"] in members:
                error = "Error: You are already in this class"
        
        if error is None:
            try:
                db.execute(
                    "INSERT INTO user_class (user_id, class_id) VALUES (?, ?)",
                    (str(g.user["id"]), str(class_id),)
                )
                db.commit()
                return redirect(url_for("class.view", class_id=class_id))
            except db.IntegrityError:
                error = "Error: User already member of class"
        
        flash(error)

    return render_template("class/code_join.html")