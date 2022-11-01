from flask import render_template, g, request, flash, redirect, url_for
from werkzeug.security import check_password_hash
from study.db import get_db
from study.auth import login_required, owner_deck_view

from .main import bp
from .validation import presence_check

def read_form():
    return request.form["password"]

def validate_data(password):
    if not presence_check(password):
        error = "Invalid password"
        flash(error)
        return False
    return True

def verify_password(password):
    correct_password = g.user["password"]
    if not check_password_hash(correct_password, password):
        error = "Incorrect password"
        flash(error)
        return False
    return True

"""Deletes deck, and all records referencing deck, e.g. terms of deck,
records of saving user and deck, records of saving class and deck, study session
with deck, spaced repetition for deck"""
def delete_deck_from_database(deck_id):
    db = get_db()
    
    # delete deck
    db.execute(
        "DELETE FROM deck WHERE id = ?",
        (str(deck_id),)
    )

    # delete records saving deck to user
    db.execute(
        "DELETE FROM save_deck WHERE deck_id = ?",
        (str(deck_id),)
    )

    # delete records saving deck to class
    db.execute(
        "DELETE FROM deck_class WHERE deck_id = ?",
        (str(deck_id),)
    )

    # delete records from study session
    db.execute(
        "DELETE FROM study_session WHERE deck_id = ?",
        (str(deck_id),)
    )

    # delete records from spaced repetition setting
    db.execute(
        "DELETE FROM spaced_repetition_setting WHERE deck_id = ?",
        (str(deck_id),)
    )

    db.commit()

def get_deck(deck_id):
    db = get_db()
    deck = db.execute(
        "SELECT * FROM deck WHERE id = ?",
        (str(deck_id),)
    ).fetchone()
    return deck

@bp.route("/delete/<deck_id>", methods=("GET", "POST"))
@login_required
@owner_deck_view
def delete(deck_id):
    if request.method == "POST":
        password = read_form()
        if validate_data(password):
            if verify_password(password):
                delete_deck_from_database(deck_id)
                return redirect(url_for("decks.all_user"))

    deck = get_deck(deck_id)

    return render_template("decks/delete.html", deck=deck)