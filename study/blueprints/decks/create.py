from flask import (
    render_template, g, request, flash, redirect, url_for
)
from study.db import get_db, to_bit
from study.auth import login_required

from .main import bp

@bp.route("/create", methods=("GET", "POST"))
@login_required
def create():
    if request.method == "POST":
        deck_name = request.form["deck_name"]
        terms = request.form["terms"]
        intra_term_delimiter = request.form["intra_term_delimiter"]
        is_public = request.form["is_public"] == "1"

        error = None
        if deck_name is None:
            error = "Deck name is required"

        if error is None:
            db = get_db()
            cursor = db.cursor()
            try:

                cursor.execute(
                    "INSERT INTO deck (owner_id, folder_id, title, is_public) VALUES (?, ?, ?, ?)",
                    (str(g.user['id']), str(g.folder["id"]), deck_name, to_bit(is_public),)
                )
                db.commit()

                deck_id = cursor.lastrowid
                for line in terms.split("\n"):
                    question, answer = line.split(intra_term_delimiter)
                    answer = answer.strip()
                    db.execute(
                        "INSERT INTO term (deck_id, question, answer) VALUES (?, ?, ?)",
                        (str(deck_id), question, answer,)
                    )
                    db.commit()

                return redirect(url_for("decks.view_deck", deck_id=deck_id))
            except db.IntegrityError:
                error = "Deck name must be unique"

        flash(error) 
    
    return render_template("decks/create.html")