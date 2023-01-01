from flask import render_template, request, redirect, url_for, flash, g
from werkzeug.security import check_password_hash

from study.auth import login_required
from study.validation import presence_check
from study.db import get_db
from .main import bp

def read_form():
    return request.form["password"]

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

def delete_spaced_repetition_setting_from_db(deck_id, routine_id):
    user_id = g.user["id"]
    db = get_db()
    db.execute(
        "DELETE FROM spaced_repetition_setting WHERE deck_Id = ? AND \
        routine_id = ? AND user_id = ?",
        (str(deck_id), str(routine_id), str(user_id),)
    )
    db.commit()

@bp.route("/delete/<deck_id>/<routine_id>", methods=("GET", "POST"))
@login_required
def delete(deck_id, routine_id):
    if request.method == "POST":
        password = read_form()

        if not presence_check(password):
            flash("Error: No password entered")
        else:
            if check_password_hash(g.user["password"], password):
                delete_spaced_repetition_setting_from_db(deck_id, routine_id)
                return redirect(url_for("spaced_repetition.list"))
            else:
               flash("Error: Incorrect password entered")

    deck = get_deck(deck_id)
    routine = get_routine(routine_id)

    return render_template("spaced_repetition/delete.html",
    deck=deck, routine=routine)