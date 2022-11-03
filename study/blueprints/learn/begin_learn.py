from flask import redirect, url_for, session
from study.auth import login_required, member_routine_view, member_deck_view
from study.db import get_db

from .main import bp

def get_smallest_term_id(deck_id):
    db = get_db()
    terms = db.execute(
        "SELECT id FROM term WHERE deck_id = ? ORDER BY id",
        (str(deck_id),)
    ).fetchall()
    smallest_id = int(terms[0]['id'])
    return smallest_id

@bp.route("/<deck_id>/<routine_id>")
@login_required
@member_deck_view
@member_routine_view
def begin_learn(deck_id, routine_id):
    smallest_term_id = get_smallest_term_id(deck_id)
    routine_position = 0
    session.pop('to_correct', None)

    return redirect(url_for("learn.learn", deck_id=deck_id, routine_id=routine_id,
     term_id=smallest_term_id, routine_position=routine_position))