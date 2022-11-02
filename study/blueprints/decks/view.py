from flask import render_template, request, g, flash
from study.db import get_db
from study.auth import login_required, member_deck_view

from .main import bp

def get_deck(deck_id):
    db = get_db()
    deck = db.execute(
        "SELECT * FROM deck WHERE id = ?",
        (str(deck_id),)
    ).fetchone()
    return deck

def get_terms(deck_id):
    db = get_db()
    terms = db.execute(
        "SELECT * FROM term WHERE deck_id = ?",
        (str(deck_id),)
    ).fetchall()
    return terms

def get_owned_routines():
    db = get_db()
    owned_routines = db.execute(
        "SELECT * FROM routine WHERE owner_id = ?",
        (str(g.user["id"]),)
    ).fetchall()
    return owned_routines

def get_class_routines():
    db = get_db()
    # gets all routines that the user has access to via a class
    # that are not owned by the user (to avoid duplicates with above list)
    class_routines = db.execute(
        "SELECT * FROM routine \
        INNER JOIN routine_class \
        ON routine.id = routine_class.routine_id \
        INNER JOIN user_class \
        ON routine_class.class_id = user_class.class_id \
        WHERE user_class.user_id = ? AND routine.owner_id != ?",
        (str(g.user["id"]), str(g.user["id"]),)
    ).fetchall()
    return class_routines

"""Returns routines that are saved to spaced repetition for this deck"""
def get_already_saved_routines(deck_id):
    db = get_db()
    already_saved_routines = db.execute(
        "SELECT * FROM spaced_repetition_setting \
        WHERE deck_id = ? AND user_id = ?",
        (str(deck_id), str(g.user["id"]),)
    ).fetchall()
    return already_saved_routines

"""Returns routines the user owns or routines saved by a class that the
user is a member of
that are not already saved to saved repetition for this deck"""
def get_routines(deck_id):
    routines = get_owned_routines() + get_class_routines()

    already_saved_routines = get_already_saved_routines(deck_id)
    already_saved_ids = [x["routine_id"] for x in already_saved_routines]

    # gets routines that are not already saved
    unsaved_routines = []
    for routine in routines:
        if routine["id"] not in already_saved_ids:
            unsaved_routines.append(routine)

    return unsaved_routines

def read_form():
    return request.form["routines"]

def save_spaced_repetition_setting(deck_id):
    db = get_db()
    routine_id = read_form()

    # inserts the setting into the database
    try:
        db.execute(
            "INSERT INTO spaced_repetition_setting (user_id, deck_id, routine_id) VALUES (?, ?, ?)",
            (str(g.user["id"]), str(deck_id), str(routine_id),)
        )
        db.commit()
    except db.IntegrityError:
        error = "Error: Deck and routine already saved to spaced repetition"
        flash(error)

@bp.route("/view/<deck_id>", methods=("POST", "GET"))
@login_required
@member_deck_view
def view_deck(deck_id):
    
    if request.method == "POST":
        if "save_to_spaced_repetition" in request.form:
            save_spaced_repetition_setting(deck_id)

    deck = get_deck(deck_id)
    terms = get_terms(deck_id)
    routines = get_routines(deck_id) # for spaced repetition

    return render_template("decks/view.html", deck=deck, terms=terms, routines=routines)