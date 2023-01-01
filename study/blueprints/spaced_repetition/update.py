from flask import render_template, g, request, flash, redirect, url_for

from study.auth import login_required
from study.db import get_db
from study.validation import range_check_exclusive, is_string_float
from .main import bp

def read_form():
    return [request.form["threshold"], request.form["steepness_constant"],
     request.form["change_constant"]]

def validate_input(threshold, steepness, change):
    """Return true if data is valid. Otherwise display error and return false"""
    # all three given values must be numerical strings greater than 0
    # treshold must be less than 1
    # TODO decide on valid ranges for steepness and change
    if not is_string_float(threshold):
        flash("Error: Threshold must be a number")
        return False
    threshold = float(threshold)
    if not range_check_exclusive(threshold, 0, 1):
        flash("Error: Threshold must be greater than 0 and less than 1")
        return False

    if not is_string_float(steepness):
        flash("Error: Steepness constant must be a number")
        return False
    
    if not is_string_float(change):
        flash("Error: Change constant must be a number")
        return False
    
    return True

def update_spaced_repetition_setting_in_db(deck_id, routine_id, threshold,
    steepness, change):
    db = get_db()
    user_id = g.user["id"]

    db.execute(
        "UPDATE spaced_repetition_setting SET reminder_threshold = ?, \
        steepness_constant = ?, change_constant = ? WHERE \
        deck_id = ? AND routine_id = ? AND user_id = ?",
        (str(threshold), str(steepness), str(change),
        str(deck_id), str(routine_id), str(user_id),)
    )
    db.commit()

def get_spaced_repetition_setting(deck_id, routine_id):
    db = get_db()
    user_id = g.user["id"]
    spaced_repetition_setting = db.execute(
        "SELECT * FROM spaced_repetition_setting WHERE \
        user_id = ? AND deck_id = ? AND routine_id = ?",
        (str(user_id), str(deck_id), str(routine_id),)
    ).fetchone()
    return spaced_repetition_setting

def get_deck(deck_id):
    db = get_db()
    deck = db.execute(
        "SELECT * FROM deck WHERE id = ?",
        (str(deck_id),)
    ).fetchone()
    return deck

def get_routine(routine_id):
    db = get_db()
    routine = db.execute(
        "SELECT * FROM routine WHERE id = ?",
        (str(routine_id),)
    ).fetchone()
    return routine

@bp.route("/update/<deck_id>/<routine_id>", methods=("GET", "POST"))
@login_required
def update(deck_id, routine_id):
    if request.method == "POST":
        threshold, steepness, change = read_form()
        if validate_input(threshold, steepness, change):
            threshold = float(threshold)
            steepness = float(steepness)
            change = float(change)

            update_spaced_repetition_setting_in_db(
                deck_id, routine_id, threshold, steepness, change)

            return redirect(url_for("spaced_repetition.view",
             deck_id=deck_id, routine_id=routine_id))

    spaced_repetition_setting = get_spaced_repetition_setting(deck_id, routine_id)
    current_threshold = spaced_repetition_setting["reminder_threshold"]
    current_steepness = spaced_repetition_setting["steepness_constant"]
    current_change = spaced_repetition_setting["change_constant"]

    current_deck = get_deck(deck_id)
    current_routine = get_routine(routine_id)

    return render_template("spaced_repetition/update.html",
     current_deck=current_deck, current_routine=current_routine,
     current_threshold=current_threshold, current_steepness=current_steepness,
     current_change=current_change)