from flask import request, render_template
from study.auth import login_required, member_routine_view, member_deck_view
from study.db import get_db
import random

from .main import bp
from .utility import add_to_queue_to_correct, get_term, record_attempt, redirect_to_next, is_answer_correct

def read_form():
    return request.form["answer"]
    return answer.replace("\r", "")

def get_other_terms(deck_id, term):
    db = get_db()
    all_terms = db.execute(
        "SELECT * FROM term WHERE deck_id = ?",
        (str(deck_id),)
    ).fetchall()
    all_terms.remove(term)
    return all_terms

def get_choices(deck_id, correct_term, amount_of_choices=3):
    """Return list of 4 to 1 terms. One term will be the given terms. Other terms
    will be randomly selected terms from the same deck"""
    # get terms from the deck (with the correct term removed)
    other_terms = get_other_terms(deck_id, correct_term)
    # randomise
    random.shuffle(other_terms)

    # if there are enough choices, just take the enough from the start
    # and put the correct term in there at a random position
    # if there are a few other terms but not as many as wanted just
    # put the correct term in there at a random position
    # if there are no other terms just return the correct term as
    # the only choice
    choices = []
    if len(other_terms) > amount_of_choices:
        choices = other_terms[0:amount_of_choices+1]
        choices[random.randint(0, len(choices)-1)] = correct_term
    elif len(other_terms) > 0:
        choices = other_terms
        choices[random.randint(0, len(choices)-1)] = correct_term
    else:
        choices = [correct_term]

    return choices


@bp.route("/<deck_id>/<routine_id>/<term_id>/<routine_position>/choice", methods=("GET", "POST"))
@login_required
@member_deck_view
@member_routine_view
def choice(deck_id, routine_id, term_id, routine_position):
    """Presents question with choice of up to 4 answers.
    Incorrect answers are randomly selected from other terms
    if there are less than 4 terms as many answers are
    retrieved as possible in a random order"""
    term = get_term(term_id)

    if request.method == "POST":
        chosen_answer = read_form()
        is_correct = is_answer_correct(chosen_answer, term)
        attempt_id = record_attempt("m", term_id, is_correct)
        if not is_correct:
            add_to_queue_to_correct(term_id, chosen_answer, attempt_id)
        return redirect_to_next(deck_id, routine_id, term_id, routine_position)

    choices = get_choices(deck_id, term)

    return render_template("learn/choice.html", correct_term=term, choices=choices)