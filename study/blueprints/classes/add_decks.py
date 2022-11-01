from flask import request, render_template, g, flash

from study.db import get_db

from .main import bp
from .view_levels import admin_level_view

def read_form():
    return request.form["deck_id"]

"""Returns decks that fit one of
- the user owns the deck AND deck is not already in class
- the user has saved the deck AND it is public AND deck is not already in class"""
def get_decks(class_id):
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
    decks_in_class = [x["deck_id"] for x in decks_in_class]

    decks_not_in_class = []
    for deck in all_decks:
        if deck["id"] not in decks_in_class:
            decks_not_in_class.append(deck)

    return decks_not_in_class

def save_deck(class_id, deck_id):
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

@admin_level_view
@bp.route("/add_decks/<class_id>", methods=("GET", "POST"))
def add_decks(class_id):
    if request.method == "POST":
        deck_id = read_form()
        save_deck(class_id, deck_id)

    decks = get_decks(class_id)

    return render_template("class/add_decks.html", decks=decks)