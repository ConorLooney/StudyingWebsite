from flask import render_template, g

from study.auth import login_required
from study.db import get_db
from .main import bp

def get_user_spaced_repetition_settings():
    user_id = g.user["id"]
    db = get_db()

    spaced_repetition_settings = db.execute(
        "SELECT * FROM spaced_repetition_setting WHERE user_id = ?",
        (str(user_id),)
    ).fetchall()

    return spaced_repetition_settings

def get_decks_dict(spaced_repetition_settings):
    """Return dictionary of deck ids to decks for each deck id of each spaced
    repetition setting in the given list"""
    db = get_db()
    decks = {}
    for spaced_repetition_setting in spaced_repetition_settings:
        deck_id = int(spaced_repetition_setting["deck_id"])
        deck = db.execute(
            "SELECT * FROM deck WHERE id = ?",
            (str(deck_id),)
        ).fetchone()
        decks[deck_id] = deck
    return decks

def get_routines_dict(spaced_repetition_settings):
    """Return dictionary of routine ids to routines for each routine id of each spaced
    repetition setting in the given list"""
    db = get_db()
    routines = {}
    for spaced_repetition_setting in spaced_repetition_settings:
        routine_id = int(spaced_repetition_setting["routine_id"])
        routine = db.execute(
            "SELECT * FROM routine WHERE id = ?",
            (str(routine_id),)
        ).fetchone()
        routines[routine_id] = routine
    return routines

@bp.route("/list")
def list():
    spaced_repetition_settings = get_user_spaced_repetition_settings()

    decks = get_decks_dict(spaced_repetition_settings)
    routines = get_routines_dict(spaced_repetition_settings)

    return render_template("spaced_repetition/list.html",
    spaced_repetition_settings=spaced_repetition_settings,
    decks=decks, routines=routines)