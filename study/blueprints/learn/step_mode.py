from flask import redirect, url_for, g, flash
from study.auth import login_required, member_routine_view, member_deck_view
from study.db import get_db

from .main import bp

def get_steps(routine_id):
    db = get_db()
    routine = db.execute(
        "SELECT steps FROM routine WHERE id = ?",
        (str(routine_id),)
    ).fetchone()
    return routine["steps"]

def get_terms(deck_id):
    """Returns the terms linked to a deck ordered by id"""
    db = get_db()
    terms = db.execute(
        "SELECT id FROM term WHERE deck_id = ? ORDER BY id",
        (str(deck_id),)
    ).fetchall()
    return terms

def get_highest_term_id(terms):
    """Returns largest term id value assuming terms are ordered by id"""
    last_term = terms[len(terms)-1]
    last_id = int(last_term["id"])
    return last_id

def get_next_term_id(terms, term_id):
    """Returns the id of the term after the term with the given id
    assuming the terms are ordered by id"""
    # stops just one before the last element to avoid index error
    for i in range(len(terms)-1):
        id = int(terms[i]["id"])
        if id == term_id:
            return terms[i + 1]["id"]
    return -1

def record_study_session(routine_id, deck_id):
    db = get_db()
    db.execute(
        "INSERT INTO study_session (user_id, routine_id, deck_id) VALUES (?, ?, ?)",
        (str(g.user["id"]), str(routine_id), str(deck_id),)
    )
    db.commit()

@bp.route("/<deck_id>/<routine_id>/<term_id>/<routine_position>", methods=("GET", "POST"))
@login_required
@member_deck_view
@member_routine_view
def step_mode(deck_id, routine_id, term_id, routine_position):
    """Redirects user to next step in routine or ends study session
    
    Routine position is the index of the step that it is currently on"""
    routine_position = int(routine_position)
    term_id = int(term_id)
    deck_id = int(deck_id)
    routine_id = int(routine_id)

    # all the steps for the current routine
    steps = get_steps(routine_id)
    amount_of_steps = len(steps)
    
    # if we are done with all the steps the position is equal to the amount of steps
    if routine_position >= amount_of_steps:
        
        terms = get_terms(deck_id)
        last_term_id = get_highest_term_id(terms)

        print(term_id)
        print(last_term_id)
        print()

        # we are done with all the steps on the last term, so we are done with everything
        # records the study session and redirects to index
        if term_id == last_term_id:
            record_study_session(routine_id, deck_id)
            return redirect(url_for("index"))
        # otherwise we are done with the steps for this term but have more terms to do
        # redirects to this function with the next term in line and back to start of routine
        else:
            next_term_id = get_next_term_id(terms, term_id)
            return redirect(url_for("learn.step_mode", deck_id=deck_id, routine_id=routine_id,
         term_id=next_term_id, routine_position=0))

    # redirects to the view for the current step
    current_step = steps[routine_position]
    step_views = {"a": "learn.ask", "c": "learn.correct", "f": "learn.flashcard",
    "m": "learn.choice", "b": "learn.fill_in_blanks"}
    if current_step in step_views:
        return redirect(url_for(step_views[current_step], deck_id=deck_id, routine_id=routine_id,
         term_id=term_id, routine_position=routine_position))
    else:
        error = "Error: Routine step does not exist"
        flash(error)

    return redirect(url_for("index"))