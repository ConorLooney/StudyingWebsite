from flask import flash
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