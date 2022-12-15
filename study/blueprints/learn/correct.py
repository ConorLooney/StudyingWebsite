from flask import request, g, session, render_template, flash
from study.auth import login_required, member_routine_view, member_deck_view
from study.db import get_db

from .main import bp
from .utility import record_attempt, is_answer_correct, pop_queue_to_correct, add_to_queue_to_correct, redirect_to_next, get_term
from study.validation import presence_check

def read_form():
    return request.form["answer"]

def unload_queue():
    """Return the term id, the given answer, and the attempt id to correct at the front of the queue"""
    to_correct_queue = session['to_correct']
    first_in_queue = to_correct_queue[0]
    term_id = first_in_queue[0]
    to_correct_answer = first_in_queue[1]
    attempt_id = first_in_queue[2]
    return term_id, to_correct_answer, attempt_id

def update_correction_queue(new_to_correct_answer):
    """Changes to answer to correct of the first correction in queue to the given answer"""
    to_correct_queue = session['to_correct']
    first_in_queue = to_correct_queue[0]
    first_in_queue[1] = new_to_correct_answer
    session['to_correct'][0] = first_in_queue

def mark_attempt_as_correct(attempt_id):
    """Sets is correct to true for the given attempt id"""
    db = get_db()
    db.execute(
        "UPDATE attempt SET is_correct = ? WHERE id = ?",
        (str(1), str(attempt_id),)
    )
    db.commit()

@bp.route("/<deck_id>/<routine_id>/<term_id>/<routine_position>/correct", methods=("GET", "POST"))
@login_required
@member_deck_view
@member_routine_view
def correct(deck_id, routine_id, term_id, routine_position):
    """Presents user with the wrong answer they gave, the question, and the correct answer
    and gets the user to type in the correct answer"""

    # if there is no queue, no need to correct anything
    if "to_correct" not in session:
        print("redirect1")
        return redirect_to_next(deck_id, routine_id, term_id, routine_position)
    to_correct_queue = session['to_correct']

    # if the queue is empty, no need to correct anything
    if len(to_correct_queue) == 0:
        session.pop("to_correct", None)
        return redirect_to_next(deck_id, routine_id, term_id, routine_position)

    term_id, to_correct_answer, attempt_id = unload_queue()
    
    term = get_term(term_id)

    if request.method == "POST":
        if "skip" in request.form:
            # skip this step as if it was never arrived upon, so no attempt recorded
            pop_queue_to_correct()
            return redirect_to_next(deck_id, routine_id, term_id, routine_position)
        elif "override" in request.form:
            # mark the ask attempt that caused this correction as correct
            # and move onto the next step
            mark_attempt_as_correct(attempt_id)
            pop_queue_to_correct()
            return redirect_to_next(deck_id, routine_id, term_id, routine_position)
        else:
            given_answer = read_form()
            if not presence_check(given_answer):
                error = "Answer is required"
                flash(error)
            else:
                is_correct = is_answer_correct(given_answer, term)
                attempt_id = record_attempt("c", term_id, is_correct)
                # if correct remove from queue and redirect
                # if incorrect set the given answer to the new given answer and
                # proceed, repeating the correction
                if is_correct:
                    pop_queue_to_correct()
                    return redirect_to_next(deck_id, routine_id, term_id, routine_position)
                else:
                    to_correct_answer = given_answer
                    update_correction_queue(to_correct_answer)

    question = term["question"]
    correct_answer = term["answer"]
    return render_template("learn/correct.html", question=question,
     to_correct_answer=to_correct_answer, actual_answer=correct_answer)