from flask import render_template, g, request, flash, redirect, url_for
from study.db import get_db, to_bit
from study.auth import login_required

from .main import bp
from study.validation import presence_check

def read_form():
    return [request.form["deck_name"],
    request.form["terms"],
    request.form["intra_term_delimiter"],
    request.form["is_public"]]

"""Returns true if data is valid otherwise displays error and returns false"""
def validate_data(deck_name, terms, intra_term_delimiter, is_public):
    # validate deck name
    if not presence_check(deck_name):
        error = "Invalid deck name"
        flash(error)
        return False

    # validate intra term delimiter
    if not presence_check(intra_term_delimiter):
        error = "Invalid value between question and answer"
        flash(error)
        return False

    # validate terms
    if not presence_check(terms):
        error = "Invalid deck terms"
        flash(error)
        return False
    terms = terms.split("\n")
    for term in terms:
        if intra_term_delimiter not in term:
            error = "Invalid deck terms: Missing marker between question and answer"
            flash(error)
            return False

    if not presence_check(is_public):
        error = "Invalid is public"
        flash(error)
        return False
    
    return True

"""Makes new term in database

Assumes data is valid"""
def insert_term_into_database(deck_id, intra_term_delimiter, line):
    db = get_db()
    question, answer = line.split(intra_term_delimiter)
    answer = answer.strip()
    db.execute(
        "INSERT INTO term (deck_id, question, answer) VALUES (?, ?, ?)",
        (str(deck_id), question, answer,)
    )
    db.commit()

"""Makes new deck in database along with the new terms, returns the new deck id

Assumes the data is valid"""
def insert_deck_into_database(deck_name, terms, intra_term_delimiter, is_public):
    db = get_db()

    cursor = db.cursor()
    cursor.execute(
        "INSERT INTO deck (owner_id, folder_id, title, is_public) VALUES (?, ?, ?, ?)",
        (str(g.user['id']), str(g.folder["id"]), deck_name, to_bit(is_public),)
    )
    db.commit()

    deck_id = cursor.lastrowid
    terms = terms.split("\n")
    for term in terms:
        insert_term_into_database(deck_id, intra_term_delimiter, term)

    return deck_id

@bp.route("/create", methods=("GET", "POST"))
@login_required
def create():
    if request.method == "POST":
        deck_name, terms, intra_term_delimiter, is_public = read_form()
        if validate_data(deck_name, terms, intra_term_delimiter, is_public):
            # convert from string to boolean
            is_public = is_public == "1"

            deck_id = insert_deck_into_database(deck_name, terms, intra_term_delimiter, is_public)

            return redirect(url_for("decks.view_deck", deck_id=deck_id))
    
    return render_template("decks/create.html")