from flask import (
    Blueprint, render_template, g, request, flash, redirect, url_for
)
from werkzeug.security import check_password_hash
from study.db import get_db
from study.auth import login_required, owner_deck_view

from .main import bp

@bp.route("/delete/<deck_id>", methods=("GET", "POST"))
@login_required
@owner_deck_view
def delete(deck_id):
    db = get_db()
    if request.method == "POST":
        password = request.form["password"]
        
        error = None

        if password is None:
            error = "Password is required"

        if error is None:
            if check_password_hash(g.user["password"], password):
                db.execute(
                    "DELETE FROM deck WHERE id = ?",
                    (str(deck_id),)
                )
                db.commit()
                db.execute(
                    "DELETE FROM save_deck WHERE deck_id = ?",
                    (str(deck_id),)
                )
                db.commit()
                return redirect(url_for("decks.all_user"))
            else:
                error = "Incorrect password"
        
        flash(error)

    deck = db.execute(
        "SELECT * FROM deck WHERE id = ?",
        (str(deck_id),)
    ).fetchone()

    return render_template("decks/delete.html", deck=deck)