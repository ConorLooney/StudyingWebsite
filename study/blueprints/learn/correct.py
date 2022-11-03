from flask import request, redirect, url_for, session, render_template, flash
from study.auth import login_required, member_routine_view, member_deck_view
from study.db import get_db

from .main import bp
from .utility import record_attempt, is_answer_correct, pop_queue_to_correct, add_to_queue_to_correct, redirect_to_next, get_term
from study.validation import presence_check

def read_form():
    return request.form["answer"]

def unload_queue():
    """Takes the first correction out of queue and returns the term id
    and the given answer to correct"""
    to_correct_queue = session['to_correct']
    first_in_queue = to_correct_queue[0]
    print(first_in_queue)
    term_id = first_in_queue[0]
    to_correct_answer = first_in_queue[1]
    pop_queue_to_correct()
    return term_id, to_correct_answer

@bp.route("/<deck_id>/<routine_id>/<term_id>/<routine_position>/correct", methods=("GET", "POST"))
@login_required
@member_deck_view
@member_routine_view
def correct(deck_id, routine_id, term_id, routine_position):
    """Presents user with the wrong answer they gave, the question, and the correct answer
    and gets the user to type in the correct answer"""

    # if there is no queue, no need to correct anything
    if "to_correct" not in session:
        return redirect_to_next(deck_id, routine_id, term_id, routine_position)
    to_correct_queue = session['to_correct']

    # if the queue is empty, no need to correct anything
    if len(to_correct_queue) == 0:
        session.pop("to_correct", None)
        return redirect_to_next(deck_id, routine_id, term_id, routine_position)

    term_id, to_correct_answer = unload_queue()
    
    term = get_term(term_id)

    if request.method == "POST":
        given_answer = read_form()
        if not presence_check(given_answer):
            error = "Answer is required"
            flash(error)
        else:
            is_correct = is_answer_correct(given_answer, term)
            record_attempt("c", term_id, is_correct)
            if not is_correct:
                add_to_queue_to_correct(term_id, given_answer)
            return redirect_to_next(deck_id, routine_id, term_id, routine_position)

    question = term["question"]
    correct_answer = term["answer"]
    return render_template("learn/correct.html", question=question,
     to_correct_answer=to_correct_answer, actual_answer=correct_answer)