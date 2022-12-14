from flask import render_template, request, redirect, url_for, g, flash
from study.auth import login_required
from study.db import get_db
from study.utility.general import save_deck_to_user
from study.utility.routine_helper import get_all_user_routines

from .main import bp
from .view_levels import member_level_view

"""Page for user to view class properties, decks, routines and modify membership

User must be logged in
User must be a member of the class

User can select a deck to study with a routine
Routines avaliable are routines saved to the class, routines saved by the user,
or routines owned by the user
If owner or admin of class, user can add and remove admins
If owner or admin of class, user can generate code to join class
If owner of admin of class, use can accept and reject join requests
If owner of admin of class, user can remove decks and routines
"""
@bp.route("/view/<class_id>", methods=("GET", "POST"))
@login_required
@member_level_view
def view(class_id):
    db = get_db()
    if request.method == "POST":
        error = None
        if "study_deck" in request.form:
            deck_id = request.form["deck_id"]
            routine_id = request.form["routines"]
            return redirect(url_for("learn.begin_learn", deck_id=deck_id, routine_id=routine_id))

        if "unsave_deck_from_class" in request.form:
            deck_id = request.form["deck_id"]
            db.execute(
                "DELETE FROM deck_class WHERE deck_id = ?",
                (str(deck_id),)
            )
            db.commit()

        if "unsave_routine_from_class" in request.form:
            routine_id = request.form["routine_id"]
            db.execute(
                "DELETE FROM routine_class WHERE routine_id = ?",
                (str(routine_id),)
            )
            db.commit()
        
        if "save_deck_to_user" in request.form:
            deck_id = request.form["deck_id"]
            save_deck_to_user(g.user["id"], deck_id)

        if "unsave_deck_from_user" in request.form:
            deck_id = request.form["deck_id"]
            db.execute(
                "DELETE FROM save_deck WHERE deck_id = ? AND user_id = ?",
                (str(deck_id), str(g.user["id"]),)
            )
            db.commit()

        if error is not None:
            flash(error)

    view_class = db.execute(
        "SELECT * FROM class WHERE id = ?",
        (str(class_id),)
    ).fetchone()

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

    saved_decks_info = []
    for deck in decks:
        if str(deck["owner_id"]) == str(g.user["id"]):
            saved_decks_info.append(-1) # cannot be saved
            continue

        save_deck = db.execute(
            "SELECT * FROM save_deck WHERE deck_id = ? AND user_id = ?",
            (str(deck["id"]), str(g.user["id"]),)
        ).fetchall()

        if len(save_deck) > 0:
            saved_decks_info.append(1) # already saved, should be unsaved
        else:
            saved_decks_info.append(0) # can be saved

    user = g.user
    
    return render_template("class/view.html",
     user=user, view_class=view_class, owner=owner, saved_decks_info=saved_decks_info, decks=decks,
      class_routines=class_routines, user_routines=user_routines,
      admins=admins)