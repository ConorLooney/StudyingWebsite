from flask import render_template, request, g

from study.db import get_db
from .main import bp
    
class Step:

    def __init__(self, name, abbreviation, accuracy=False):
        self.name = name
        self.abbreviation = abbreviation
        self.accuracy = accuracy

def get_deck(deck_id):
    db = get_db()
    deck = db.execute(
        "SELECT * FROM deck WHERE id = ?",
        (str(deck_id),)
    ).fetchone()
    return deck

def get_routines_studied_with(deck_id):
    """Return all routines the logged in user has studied the given
    deck with"""
    db = get_db()
    routines = db.execute(
        "SELECT DISTINCT routine.id, title FROM routine \
        JOIN study_session ON routine.id = study_session.routine_id \
        WHERE study_session.deck_id = ? AND study_session.user_id = ?",
        (str(deck_id), str(g.user["id"]),)
    ).fetchall()
    return routines

def get_amount_of_times_routine_was_studied_with(routine_id, deck_id):
    """Return number of times the given deck was studied with the given routine
    by the logged in user"""
    db = get_db()
    sessions = db.execute(
        "SELECT * FROM study_session \
        WHERE routine_id = ? AND deck_id = ? AND user_id = ?",
        (str(routine_id), str(deck_id), str(g.user["id"]),)
    ).fetchall()
    return len(sessions)

def get_terms(deck_id):
    db = get_db()
    terms = db.execute(
        "SELECT * FROM term WHERE deck_id = ?",
        (str(deck_id),)
    ).fetchall()
    return terms

def get_amount_of_times_term_was_studied_with_step(term_id, step):
    db = get_db()
    attempts = db.execute(
        "SELECT * FROM attempt WHERE term_id = ? AND step = ? AND user_id = ?",
        (str(term_id), str(step.abbreviation), str(g.user["id"]))
    ).fetchall()
    return len(attempts)

def get_accuracy_term_studied_with_step(term_id, step):
    """Return prorportion of attempts on given term with given step that were correct"""
    total = get_amount_of_times_term_was_studied_with_step(term_id, step)
    db = get_db()
    correct = db.execute(
        "SELECT * FROM attempt WHERE term_id = ? AND step = ? AND user_id = ? AND is_correct = 1",
        (str(term_id), str(step.abbreviation), str(g.user["id"]),)
    ).fetchall()
    return len(correct) / total

@bp.route("/view/<deck_id>", methods=("GET", "POST"))
def view(deck_id):
    steps = [
        Step("Ask", "a", accuracy=True),
        Step("Correct", "c", accuracy=True),
        Step("Flashcard", "f", accuracy=False),
        Step("Multiple Choice", "m", accuracy=True),
        Step("Copy", "y", accuracy=True),
        Step("Fill in Blanks", "b", accuracy=True)
    ]

    routines = get_routines_studied_with(deck_id)
    overall_stats = []
    for routine in routines:
        title = routine["title"]
        frequency = get_amount_of_times_routine_was_studied_with(routine["id"], deck_id)
        message = f"Studied with {title} {frequency} times"
        overall_stats.append(message)
        
    terms = get_terms(deck_id)
    terms_messages = {}
    for term in terms:
        messages = []
        for step in steps:
            message = ""
            step_name = step.name
            frequency = get_amount_of_times_term_was_studied_with_step(term["id"], step)
            message += f"Studied with { step_name } { frequency } times"
            if step.accuracy and frequency != 0:
                accuracy = get_accuracy_term_studied_with_step(term["id"], step)
                percent_correct = round(accuracy * 100, 1)
                message += f", and { percent_correct }% of the time you were correct"
            if frequency != 0:
                messages.append(message)
        terms_messages[term["id"]] = messages

    deck = get_deck(deck_id)

    return render_template("statistics/view.html", deck=deck,
    overall_stats=overall_stats, terms=terms, terms_messages=terms_messages)