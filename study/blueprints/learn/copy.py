from flask import request, render_template, flash
from study.auth import login_required, member_routine_view, member_deck_view

from .main import bp
from study.validation import presence_check
from .utility import record_attempt, add_to_queue_to_correct, is_answer_correct, redirect_to_next, get_term

def read_form():
    return request.form["answer"]

@bp.route("/<deck_id>/<routine_id>/<term_id>/<routine_position>/copy", methods=("GET", "POST"))
@login_required
@member_deck_view
@member_routine_view
def copy(deck_id, routine_id, term_id, routine_position):

    term = get_term(term_id)

    if request.method == "POST":
        given_answer = read_form()

        if not presence_check(given_answer):
            error = "Error: No answer given"
            flash(error)
        else:
            is_correct = is_answer_correct(given_answer, term)
            attempt_id = record_attempt("a", term_id, is_correct)
            if not is_correct:
                add_to_queue_to_correct(term_id, given_answer, attempt_id)
            else:
                return redirect_to_next(deck_id, routine_id, term_id, routine_position)

    return render_template("learn/copy.html", term=term)