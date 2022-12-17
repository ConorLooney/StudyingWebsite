from flask import redirect, url_for, g, flash
from study.auth import login_required, member_routine_view, member_deck_view

from study.db import get_db
from .main import bp
from .steps import does_step_run_once_per_session, get_step_view_func_from_abbreviation
from .utility import redirect_to_next

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

# TODO: move shared functions into shared file. Test?

@bp.route("/b/<deck_id>/<routine_id>/<term_id>/<routine_position>", methods=("GET", "POST"))
@login_required
@member_deck_view
@member_routine_view
def term_mode(deck_id, routine_id, term_id, routine_position):
    """Argument names are the same as learn but values are different TODO: make this make sense
    these values would be passed from a redirecting learn function because this increments the term,
    however that is not done simply by incrementing the term id. therefore that logic is done here
    this function takes in the current values and moves onto the next term and or routine or ends the session
    
    If term_id is -1, a rogue value, then it is taken to mean the first term, i.e. the smallest, meaning
    this is how to begin a learning session using term mode"""
    routine_position = int(routine_position)
    term_id = int(term_id)
    deck_id = int(deck_id)
    routine_id = int(routine_id)
    terms = get_terms(deck_id)

    # all the steps for the current routine
    steps = get_steps(routine_id)
    amount_of_steps = len(steps)
    current_step = steps[routine_position]

    if term_id == -1: # no term has been completed, get first term
        next_term = get_smallest_term_id(deck_id)
    else:
        next_term = get_next_term_id(terms, term_id)

    # if next term is -1 then there are no more terms
    # reset term counter and move onto next routine step
    # if there are no more routine steps end the session
    if next_term == -1:
        next_term = get_smallest_term_id(deck_id)
        routine_position += 1
        if routine_position >= amount_of_steps:
            record_study_session(routine_id, deck_id)
            return redirect(url_for("index"))

    if does_step_run_once_per_session(current_step):
        # if this term is not the first term to run, then 
        # it should be skipped as this step only runs once per session
        if not next_term == get_smallest_term_id(deck_id):
            return redirect_to_next(deck_id, routine_id, get_highest_term_id(terms), routine_position)

    step_function = get_step_view_func_from_abbreviation(current_step)
    return redirect(url_for(step_function, deck_id=deck_id, routine_id=routine_id,
        term_id=next_term, routine_position=routine_position))