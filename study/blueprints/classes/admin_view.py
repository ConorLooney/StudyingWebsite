from flask import render_template, request, redirect, url_for, g
from study.db import get_db
from study.utility.general import remove_user_from_class, get_all_user_routines

from .main import bp
from .view_levels import admin_level_view

"""Page for adding and removing class mebers, admins, decks, and routines

Only allowed to view if you own a class or you are an admin

Sees list of class members
Can remove member
Sees list of class admins
Can unadmin admin
Sees list of join requests
Can accept or reject request
Can generate join code
Can see list of decks and unsave them from class
Can see list of routines and unsave them from class"""
@bp.route("/admin_view/<class_id>", methods=("GET", "POST"))
@admin_level_view
def admin_view(class_id):
    db = get_db()
    if request.method == "POST":
        error = None

        
        if "remove_user" in request.form:
            user_id = request.form["user_id"]
            remove_user_from_class(user_id, class_id)
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
        if "unsave_deck" in request.form:
            deck_id = request.form["deck_id"]
            db.execute(
                "DELETE FROM deck_class WHERE deck_id = ? AND class_id = ?",
                (str(deck_id), str(class_id),)
            )
            db.commit()
        if "unsave_routine_from_class" in request.form:
            routine_id = request.form["routine_id"]
            db.execute(
                "DELETE FROM routine_class WHERE routine_id = ? AND class_id = ?",
                (str(routine_id), str(class_id),)
            )
            db.commit()
        
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

    decks = db.execute(
        "SELECT * FROM deck \
        JOIN deck_class ON deck_class.deck_id = deck.id \
        WHERE deck_class.class_id = ?",
        (str(class_id),)
    ).fetchall()

    class_routines = db.execute(
        "SELECT * FROM routine \
        JOIN routine_class ON routine_class.routine_id = routine.id \
        WHERE routine_class.class_id = ?",
        (str(class_id),)
    ).fetchall()
    user_routines = get_all_user_routines(g.user["id"])

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
    is_admin =  str(g.user["id"]) in [str(x["id"]) for x in admins]

    return render_template("class/admin_view.html", user=user, view_class=view_class, owner=owner, decks=decks,
      class_routines=class_routines, user_routines=user_routines, members=members,
      admins=admins, is_owner=is_owner, is_admin=is_admin, join_requests=join_requests)