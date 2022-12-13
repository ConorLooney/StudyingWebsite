from flask import session, g, redirect, url_for
from study.db import get_db, to_bit

def record_study_session(routine_id, deck_id):
    db = get_db()
    user_id = g.user["id"]
    db.execute(
        "INSERT INTO study_session (user_id, routine_id, deck_id) VALUES (?, ?, ?)",
        (str(user_id), str(routine_id), str(deck_id),)
    )
    db.commit()

def record_attempt(step, term_id, is_correct):
    """Records an attempt of the given step and term"""
    db = get_db()
    db.execute(
        "INSERT INTO attempt (step, term_id, user_id, is_correct) VALUES (?, ?, ?, ?)",
        (step, str(term_id), str(g.user["id"]), str(to_bit(is_correct)),)
    )
    db.commit()

def add_to_queue_to_correct(term_id, given_answer):
    """Adds new item to correct at end of queue
    
    Takes the term id and the answer the user gave to be corrected"""
    if "to_correct" not in session:
        session["to_correct"] = []
    session['to_correct'].append([term_id, given_answer])
    session.modified = True

def pop_queue_to_correct():
    """Removes the first in element of the queue (queue, so first in, first out)"""
    session['to_correct'].remove(session['to_correct'][0])
    session.modified = True

def is_answer_correct(given_answer, term):
    """Strips of whitespace the given answer and the term's answer and compares"""
    return given_answer.strip() == term["answer"].strip()

def redirect_to_next(deck_id, routine_id, term_id, routine_position):
    """Returns redirect to learn with incremented routine position"""
    #routine_position = int(routine_position) + 1
    #return redirect(url_for("learn.learn", deck_id=deck_id, routine_id=routine_id,
    #    term_id=term_id, routine_position=routine_position))
    return redirect(url_for("learn.batch_learn", deck_id=deck_id, routine_id=routine_id,
        term_id=term_id, routine_position=routine_position))

def get_term(term_id):
    db = get_db()
    term = db.execute(
        "SELECT * FROM term WHERE id = ?",
        (str(term_id),)
    ).fetchone()
    return term
