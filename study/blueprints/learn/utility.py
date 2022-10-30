from flask import session, g
from study.db import get_db

def record_study_session(routine_id, deck_id):
    db = get_db()
    user_id = g.user["id"]
    db.execute(
        "INSERT INTO study_session (user_id, routine_id, deck_id) VALUES (?, ?, ?)",
        (str(user_id), str(routine_id), str(deck_id),)
    )
    db.commit()

def queue_to_correct(term_id, given_answer):
    session['to_correct'].append([term_id, given_answer])
    session.modified = True

def pop_queue_to_correct():
    session['to_correct'].remove(session['to_correct'][0])
    session.modified = True

