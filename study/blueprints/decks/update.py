from flask import (
    render_template, g, request, flash, redirect, url_for
)
from study.db import get_db, to_bit
from study.auth import login_required, owner_deck_view

from .main import bp

@bp.route("/update/<deck_id>", methods=("GET", "POST"))
@login_required
@owner_deck_view
def update(deck_id):
    db = get_db()

    if request.method == "POST":
        deck_name = request.form["deck_name"]
        terms = request.form["terms"]
        intra_term_delimiter = request.form["intra_term_delimiter"]
        is_public = request.form["is_public"] == "1"

        error = None
        if deck_name is None:
            error = "Deck name is required"

        if error is None:
            db.execute(
                "UPDATE deck SET title = ?, is_public = ?, modified = CURRENT_TIMESTAMP WHERE id = ?",
                (deck_name, to_bit(is_public), str(deck_id),)
            )
            db.commit()

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

            return redirect(url_for("decks.view_deck", deck_id=deck_id))

        flash(error) 

    current_deck = db.execute(
        "SELECT * FROM deck WHERE id = ?",
        (str(deck_id),)
    ).fetchone()

    terms = db.execute(
        "SELECT * FROM term WHERE deck_id = ?",
        (str(deck_id),)
    ).fetchall()

    return render_template("decks/update.html", deck=current_deck, terms=terms)