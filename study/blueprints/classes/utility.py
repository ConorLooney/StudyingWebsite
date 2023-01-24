from flask import flash, g
from study.db import get_db
from study.validation import presence_check

def validate_data(title, description, is_public):
    """Validates the data used for a class"""
    if not presence_check(title):
        error = "Error: Name for class is required"
        flash(error)
        return False
    
    if not presence_check(description):
        error = "Error: Description of class is required"
        flash(error)
        return False

    if not presence_check(is_public):
        error = "Error: Whether class is public or not is required"
        flash(error)
        return False

    return True

def new_class_member_in_database(class_id, user_id):
    """Creates a new record of the class membership and returns false if the
    user is already in this class (and displays this error) otherwise returns true"""
    db = get_db()
    try:
        db.execute(
            "INSERT INTO user_class (user_id, class_id) VALUES (?, ?)",
            (str(user_id), str(class_id),)
        )
        db.commit()
    except db.IntegrityError:
        error = "Error: User already a member of the class"
        flash(error)
        return False
    return True

def save_deck_to_class(class_id, deck_id):
    db = get_db()
    try:
        db.execute(
            "INSERT INTO deck_class (deck_id, class_id) VALUES (?, ?)",
            (str(deck_id), str(class_id))
        )
        db.commit()
    except db.IntegrityError:
        error = "Error: Deck already saved to class"
        flash(error)

def get_decks_to_add_to_class(class_id):
    """Return all decks that are owned or saved by user that are not in the class"""
    db = get_db()

    user_id = g.user["id"]
    user_owned_decks = db.execute(
        "SELECT * FROM deck WHERE owner_id = ?",
        (str(user_id),)
    ).fetchall()

    user_saved_decks = db.execute(
        "SELECT * FROM deck INNER JOIN save_deck \
        ON deck.id = save_deck.deck_id \
        WHERE deck.is_public = 1 AND save_deck.user_id = ?",
        (str(user_id),)
    ).fetchall()

    all_decks = user_owned_decks + user_saved_decks

    decks_in_class = db.execute(
        "SELECT deck_id FROM deck_class WHERE class_id = ?",
        (str(class_id),)
    ).fetchall()
    deck_ids_in_class = [x["deck_id"] for x in decks_in_class]

    decks_not_in_class = []
    for deck in all_decks:
        if deck["id"] not in deck_ids_in_class:
            decks_not_in_class.append(deck)

    return decks_not_in_class

def get_routines_to_save_to_class(class_id):
    """Return all routines owned by user not in class"""
    db = get_db()

    routines = db.execute(
        "SELECT * FROM routine WHERE owner_id = ?",
        (str(g.user["id"]),)
    ).fetchall()

    routines_in_class = db.execute(
        "SELECT routine_id FROM routine_class WHERE class_id = ?",
        (str(class_id),)
    ).fetchall()
    routines_in_class = [x["routine_id"] for x in routines_in_class]

    routines_not_in_class = []
    for routine in routines:
        if routine["id"] not in routines_in_class:
            routines_not_in_class.append(routine)

    return routines_not_in_class

def save_routine_to_class(class_id, routine_id):
    db = get_db()
    try:
        db.execute(
            "INSERT INTO routine_class (routine_id, class_id) VALUES (?, ?)",
            (str(routine_id), str(class_id))
        )
        db.commit()
    except db.IntegrityError:
        error = "Error: routine already saved to class"
        flash(error)

def get_decks_to_remove_from_class(class_id):
    db = get_db()
    decks = db.execute(
        "SELECT * FROM deck \
        JOIN deck_class ON deck_class.deck_id = deck.id \
        WHERE deck_class.class_id = ?",
        (str(class_id),)
    ).fetchall()
    return decks

def get_routines_to_remove_from_class(class_id):
    db = get_db()
    routines = db.execute(
        "SELECT * FROM routine \
        JOIN routine_class ON routine_class.routine_id = routine.id \
        WHERE routine_class.class_id = ?",
        (str(class_id),)
    ).fetchall()
    return routines

def remove_deck_from_class(class_id, deck_id):
    db = get_db()
    db.execute(
        "DELETE FROM deck_class WHERE deck_id = ? AND class_id = ?",
        (str(deck_id), str(class_id),)
    )
    db.commit()

def remove_routine_from_class(class_id, routine_id):
    db = get_db()
    db.execute(
        "DELETE FROM routine_class WHERE routine_id = ? AND class_id = ?",
        (str(routine_id), str(class_id),)
    )
    db.commit()