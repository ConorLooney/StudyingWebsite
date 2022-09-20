from flask import (
    flash, session, g
)
from study.db import get_db, to_bool
from study.utility.folder import get_user_root_folder

"""Can be used to get saved info for classes, decks, and routines"""
def get_saved_info(objects, object_table, user_id):
    if object_table not in ["deck", "routine", "class"]:
        error = "Error: Invalid saved information request"
        flash(error)
        return []

    db = get_db()
    saved_info = []
    for object in objects:
        if str(object["owner_id"]) == str(user_id):
            saved_info.append(-1) # cannot be saved
            continue

        if object_table == "class":
            saved_instance = db.execute(
                "SELECT * FROM user_class \
                WHERE class_id = ? AND user_id = ?",
                (str(object["id"]), str(user_id),)
            ).fetchall()
        else:
            saved_instance = db.execute(
                "SELECT * FROM save_" + object_table + " \
                WHERE " + object_table + "_id = ? AND user_id = ?",
                (str(object["id"]), str(user_id),)
            ).fetchall()

        if len(saved_instance) > 0:
            saved_info.append(1) # already saved, should be unsaved
        else:
            saved_info.append(0) # can be saved
    return saved_info

def get_all_user_controlled_classes(user_id):
    db = get_db()
    classes = db.execute(
        "SELECT * FROM class WHERE owner_id = ?",
        (str(user_id),)
    ).fetchall()
    classes.extend(db.execute(
        "SELECT * FROM class \
        JOIN admin_class ON class.id = admin_class.class_id \
        WHERE admin_class.admin_id = ?",
        (str(user_id),)
    ).fetchall())
    return classes

def get_all_user_decks(user_id, folder_id):
    db = get_db()
    decks = db.execute(
        "SELECT * FROM deck WHERE owner_id = ? AND folder_id = ?",
        (str(user_id), str(folder_id),)
    ).fetchall()
    decks.extend(db.execute(
        "SELECT * FROM deck \
        JOIN save_deck ON save_deck.deck_id = deck.id \
        WHERE save_deck.user_id = ? AND save_deck.folder_id = ?",
        (str(user_id), str(folder_id),)
    ).fetchall())
    return decks

def get_all_user_routines(user_id):
    db = get_db()
    routines = db.execute(
        "SELECT * FROM routine WHERE owner_id = ?",
        (str(user_id),)
    ).fetchall()
    routines.extend(db.execute(
        "SELECT * FROM routine \
        JOIN save_routine ON save_routine.routine_id = routine.id \
        WHERE save_routine.user_id = ?",
        (str(user_id),)
    ).fetchall())
    return routines

def delete_class(class_id):
    db = get_db()
    db.execute(
        "DELETE FROM class WHERE id = ?",
        (str(class_id),)
    )
    db.execute(
        "DELETE FROM user_class WHERE class_id = ?",
        (str(class_id),)
    )
    db.execute(
        "DELETE FROM admin_class WHERE class_id = ?",
        (str(class_id),)
    )
    db.execute(
        "DELETE FROM deck_class WHERE class_id = ?",
        (str(class_id),)
    )
    db.execute(
        "DELETE FROM routine_class WHERE class_id = ?",
        (str(class_id),)
    )
    db.execute(
        "DELETE FROM invite_code WHERE class_id = ?",
        (str(class_id),)
    )
    db.execute(
        "DELETE FROM join_request WHERE class_id = ?",
        (str(class_id),)
    )
    db.commit()

def save_deck_to_class(class_id, deck_id):
    db = get_db()
    error = None
    try:
        db.execute(
            "INSERT INTO deck_class (deck_id, class_id) VALUES (?, ?)",
            (str(deck_id), str(class_id))
        )
        db.commit()
    except db.IntegrityError:
        error = "Error: Deck already saved to class"
    if error:
        flash(error)

def add_user_to_class(user_id, class_id):
    db = get_db()
    error = None
    try:
        db.execute(
            "INSERT INTO user_class (user_id, class_id) VALUES (?, ?)",
            (str(user_id), str(class_id),)
        )
        db.commit()
    except db.IntegrityError:
        error = "Error: User already in class"
    if error:
        flash(error)
    db.commit()

def remove_user_from_class(user_id, class_id):
    db = get_db()
    db.execute(
        "DELETE FROM user_class WHERE user_id = ? AND class_id = ?",
        (str(user_id), str(class_id),)
    )
    db.execute(
        "DELETE FROM admin_class WHERE admin_id = ? AND class_id = ?",
        (str(user_id), str(class_id),)
    )
    db.commit()

def save_deck_to_user(user_id, deck_id, folder_id=None):
    if folder_id is None:
        folder_id = get_user_root_folder(user_id)["id"]
    db = get_db()
    error = None

    deck = db.execute(
        "SELECT * FROM deck WHERE id = ?",
        (str(deck_id),)
    ).fetchone()

    if str(deck["owner_id"]) == str(user_id):
        error = "Error: Cannot save deck you own"

    if not to_bool(deck["is_public"]):
        error = "Error: Cannot save private deck"

    if error is None:
        try:
            db.execute(
                "INSERT INTO save_deck (user_id, deck_id, folder_id) VALUES (?, ?, ?)",
                (str(user_id), str(deck_id), str(folder_id),)
            )
            db.commit()
        except db.IntegrityError:
            error = "Error: User has already saved deck"

    if error is not None:
        flash(error)

def unsave_deck_from_user(user_id, deck_id):
    db = get_db()
    db.execute(
        "DELETE FROM save_deck WHERE deck_id = ? AND user_id = ?",
        (str(deck_id), str(user_id),)
    )
    db.commit()

def save_routine_to_class(class_id, routine_id):
    db = get_db()
    error = None
    try:
        db.execute(
            "INSERT INTO routine_class (routine_id, class_id) VALUES (?, ?)",
            (str(routine_id), str(class_id),)
        )
        db.commit()
    except db.IntegrityError:
        error = "Error: Routine already saved to class"
    if error:
        flash(error)

def save_routine_to_user(user_id, routine_id):
    db = get_db()
    error = None

    routine = db.execute(
        "SELECT * FROM routine WHERE id = ?",
        (str(routine_id),)
    ).fetchone()

    if str(routine["owner_id"]) == str(user_id):
        error = "Error: Cannot save routine you own"

    if not to_bool(routine["is_public"]):
        error = "Error: Cannot save private routine"

    if error is None:
        try:
            db.execute(
                "INSERT INTO save_routine (user_id, routine_id) VALUES (?, ?)",
                (str(user_id), str(routine_id),)
            )
            db.commit()
        except db.IntegrityError:
            error = "Error: User has already saved routine"

    if error is not None:
        flash(error)

def unsave_routine_from_user(user_id, routine_id):
    db = get_db()
    db.execute(
        "DELETE FROM save_routine WHERE user_id = ? AND routine_id = ?",
        (str(user_id), str(routine_id),)
    )
    db.commit()