from flask import redirect, url_for
from study.auth import login_required, member_routine_view, member_deck_view
from study.db import get_db

from .main import bp

def record_study_session(routine_id, deck_id):
    db = get_db()
    user_id = g.user["id"]
    db.execute(
        "INSERT INTO study_session (user_id, routine_id, deck_id) VALUES (?, ?, ?)",
        (str(user_id), str(routine_id), str(deck_id),)
    )
    db.commit()

@bp.route("/<deck_id>/<routine_id>/<term_id>/<routine_position>", methods=("GET", "POST"))
@login_required
@member_deck_view
@member_routine_view
def learn(deck_id, routine_id, term_id, routine_position):
    routine_position = int(routine_position)

    db = get_db()
    steps = db.execute(
        "SELECT steps FROM routine WHERE id = ?",
        (str(routine_id),)
    ).fetchone()['steps']
    
    amount_of_steps = len(steps)
    if routine_position >= amount_of_steps:
        term_id = int(term_id)
        terms = db.execute(
            "SELECT id FROM term WHERE deck_id = ? ORDER BY id",
            (str(deck_id),)
        ).fetchall()

        if term_id == terms[len(terms)-1]["id"]:
            record_study_session(routine_id, deck_id)
            return redirect(url_for("/index"))
        else:
            for i in range(len(terms)):
                if terms[i]["id"] == term_id:
                    next_term_id = terms[i + 1]["id"]
            return redirect(url_for("learn.learn", deck_id=deck_id, routine_id=routine_id,
         term_id=next_term_id, routine_position=0))

    current_step = steps[routine_position]
    step_views = {"a": "learn.ask", "c": "learn.correct", "f": "learn.flashcard",
    "m": "learn.choice", "b": "learn.fill_in_blanks"}
    if current_step in step_views:
        return redirect(url_for(step_views[current_step], deck_id=deck_id, routine_id=routine_id,
         term_id=term_id, routine_position=routine_position))

    return redirect(url_for("/index"))