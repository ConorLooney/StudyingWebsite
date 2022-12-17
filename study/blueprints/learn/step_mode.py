from flask import redirect, url_for, g, flash
from study.auth import login_required, member_routine_view, member_deck_view
from study.db import get_db

from .steps import get_step_view_func_from_abbreviation, does_step_run_once_per_session
from .utility import redirect_to_next
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

def get_smallest_term_id(deck_id):
    db = get_db()
    terms = db.execute(
        "SELECT id FROM term WHERE deck_id = ? ORDER BY id",
        (str(deck_id),)
    ).fetchall()
    smallest_id = int(terms[0]['id'])
    return smallest_id

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

    current_step = steps[routine_position]

    if does_step_run_once_per_session(current_step):
        # this step only runs once per session
        # if we are at the first term right now then that is fine
        # but if this is not the first term then this step has run before
        # so skip this step if this term is not the first
        if not term_id == get_smallest_term_id(deck_id):
            # redirec to next automatically increments routine pos
            return redirect_to_next(deck_id, routine_id, term_id, routine_position)
    
    step_function = get_step_view_func_from_abbreviation(current_step)
    return redirect(url_for(step_function, deck_id=deck_id, routine_id=routine_id,
        term_id=term_id, routine_position=routine_position))