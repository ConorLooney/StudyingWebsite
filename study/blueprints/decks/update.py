from flask import render_template, request, flash, redirect, url_for
from study.db import get_db, to_bit
from study.auth import login_required, owner_deck_view

from .main import bp
from .create import validate_data

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

def read_form():
    return [
        request.form["deck_name"],
        request.form["terms"],
        request.form["intra_term_delimiter"],
        request.form["is_public"],
    ]

def update_deck_in_database(deck_id, deck_name, is_public):
    db = get_db()
    db.execute(
        "UPDATE deck SET title = ?, is_public = ?, modified = CURRENT_TIMESTAMP WHERE id = ?",
        (deck_name, to_bit(is_public), str(deck_id),)
    )
    db.commit()

def replace_terms_in_database(deck_id, terms, intra_term_delimiter):
    db = get_db()
    # deletes old terms
    db.execute(
        "DELETE FROM term WHERE deck_id = ?",
        (str(deck_id),)
    )
    db.commit()

    for line in terms.split("\n"):
        question, answer = line.split(intra_term_delimiter)
        db.execute(
            "INSERT INTO term (deck_id, question, answer) VALUES (?, ?, ?)",
            (str(deck_id), question, answer,)
        )
    db.commit()

@bp.route("/update/<deck_id>", methods=("GET", "POST"))
@login_required
@owner_deck_view
def update(deck_id):
    if request.method == "POST":
        deck_name, terms, intra_term_delimiter, is_public = read_form()

        if validate_data(deck_name, terms, intra_term_delimiter, is_public):

            is_public = request.form["is_public"] == "1"

            update_deck_in_database(deck_id, deck_name, is_public)
            replace_terms_in_database(deck_id, terms, intra_term_delimiter)

            return redirect(url_for("decks.view_deck", deck_id=deck_id))

    deck = get_deck(deck_id)
    terms = get_terms(deck_id)

    return render_template("decks/update.html", deck=deck, terms=terms)