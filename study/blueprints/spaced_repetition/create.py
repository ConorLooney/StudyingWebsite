from flask import render_template, g, request, flash, redirect, url_for

from study.auth import login_required
from study.db import get_db
from study.utility.helper import remove_duplicate_rows
from study.validation import range_check_exclusive, is_string_float
from .main import bp

## TODO Organise these functions into utility files as they are used by different
## views for similar purposes. Should not be repeated in different files.

def get_classes_user_is_in():
    user_id = g.user["id"]
    db = get_db()

    classes_user_is_in = db.execute(
        "SELECT * FROM class \
        INNER JOIN user_class \
        ON class.id = user_class.class_id \
        WHERE user_class.user_id = ?",
        (str(user_id),)
    ).fetchall()

    return classes_user_is_in

def get_owned_decks():
    user_id = g.user["id"]
    db = get_db()
    owned = db.execute(
        "SELECT * FROM deck WHERE owner_id = ?",
        (str(user_id),)
    ).fetchall()
    return owned

def get_saved_decks():
    user_id = g.user["id"]
    db = get_db()
    saved = db.execute(
        "SELECT * FROM deck \
        INNER JOIN save_deck \
        ON deck.id = save_deck.deck_id \
        WHERE save_deck.user_id = ?",
        (str(user_id),)
    ).fetchall()
    return saved

def get_class_decks():
    db = get_db()

    classes_user_is_in = get_classes_user_is_in()

    decks = []
    for class_user_is_in in classes_user_is_in:
        class_id = class_user_is_in["id"]
        decks_in_class = db.execute(
            "SELECT * FROM deck \
            INNER JOIN deck_class \
            ON deck_class.deck_id = deck.id \
            WHERE deck_class.class_id = ?",
            (str(class_id),)
        ).fetchall()
        decks += decks_in_class
    return decks

def get_owned_routines():
    user_id = g.user["id"]
    db = get_db()

    routines = db.execute(
        "SELECT * FROM routine WHERE owner_id = ?",
        (str(user_id),)
    ).fetchall()

    return routines

def get_class_routines():
    user_id = g.user["id"]
    db = get_db()

    classes_user_is_in = get_classes_user_is_in() 

    routines = []
    for class_user_is_in in classes_user_is_in:
        class_id = class_user_is_in["id"]
        class_routines = db.execute(
            "SELECT * FROM routine \
            INNER JOIN routine_class \
            ON routine_class.routine_id = routine.id \
            WHERE routine_class.class_id = ?",
            (str(class_id),)
        ).fetchall()
        routines += class_routines

    return routines

def read_form():
    return [request.form["deck"], request.form["routine"], request.form["threshold"],
    request.form["steepness_constant"], request.form["change_constant"]]

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

def insert_spaced_repetition_setting_into_db(deck_id, routine_id, threshold,
    steepness, change):
    """Insert new spaced repetition setting into database with given values.
    Return true if no error and false otherwise"""
    db = get_db()
    user_id = g.user["id"]

    try:
        db.execute(
            "INSERT INTO spaced_repetition_setting (user_id, deck_id, routine_id, \
            reminder_threshold, steepness_constant, change_constant) VALUES \
            (?, ?, ?, ?, ?, ?)",
            (str(user_id), str(deck_id), str(routine_id), str(threshold),
            str(steepness), str(change),)
        )
        db.commit()
        return True
    except db.IntegrityError:
        error = "Error: Spaced repetition setting already exists for this deck and routine. Either update that setting's values or delete that setting and try again."
        flash(error)
        return False

@bp.route("/create", methods=("GET", "POST"))
@login_required
def create():
    if request.method == "POST":
        deck_id, routine_id, threshold, steepness, change = read_form()
        # deck_id and routine_id do not need to be validated as they are selected
        if validate_input(threshold, steepness, change):
            threshold = float(threshold)
            steepness = float(steepness)
            change = float(change)
            if insert_spaced_repetition_setting_into_db(
                deck_id, routine_id, threshold, steepness, change):
                return redirect(url_for("spaced_repetition.view",
                deck_id=deck_id, routine_id=routine_id))
    
    decks = get_class_decks() + get_saved_decks() + get_owned_decks()
    decks = remove_duplicate_rows(decks, "id")
    routines = get_owned_routines() + get_class_routines()

    return render_template("spaced_repetition/create.html",
    decks=decks, routines=routines)