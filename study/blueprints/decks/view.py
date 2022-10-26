from flask import (
    render_template
)
from study.db import get_db
from study.auth import login_required, member_deck_view

from .main import bp

@bp.route("/view/<deck_id>")
@login_required
@member_deck_view
def view_deck(deck_id):
    db = get_db()
    deck = db.execute(
        "SELECT * FROM deck WHERE id = ?",
        (str(deck_id),)
    ).fetchone()

    terms = db.execute(
        "SELECT * FROM term WHERE deck_id = ?",
        (str(deck_id),)
    ).fetchall()

    return render_template("decks/deck.html", deck=deck, terms=terms)