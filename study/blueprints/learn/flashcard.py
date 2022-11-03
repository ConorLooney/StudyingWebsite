from flask import request, redirect, url_for, session, render_template, g
from study.auth import login_required, member_routine_view, member_deck_view
from study.db import get_db, to_bit

from .main import bp
from .utility import redirect_to_next, record_attempt, get_term

@bp.route("/<deck_id>/<routine_id>/<term_id>/<routine_position>/flashcard/", methods=("GET", "POST"))
@bp.route("/<deck_id>/<routine_id>/<term_id>/<routine_position>/flashcard/<question_facing>/", methods=("GET", "POST"))
@login_required
@member_deck_view
@member_routine_view
def flashcard(deck_id, routine_id, term_id, routine_position, question_facing=1):
    # the question facing defaults to True as initially the question faces up
    # this view displays either the question or answer depending on if
    # question facing is 1 or 0
    # when the user hits flip this function redirects to itself with a flipped
    # value of question facing

    # in this way no session or cookie data is stored, just a local variable
    # and redirects
    # although it means another url rotues to this function without the question
    # facing option so that learn can route to this function without making a 
    # special case for this function

    question_facing = int(question_facing)
    term = get_term(term_id)

    if request.method == "POST":
        # record attempt (is correct is just recorded as true, doesn't matter)
        record_attempt("f", term_id, True)

        if "flip" in request.form:
            # if the question is currently facing redirect to this function except
            # make the question face down, ie make it show the answer
            if question_facing == 1:
                return redirect(url_for("learn.flashcard", deck_id=deck_id,
                routine_id=routine_id, term_id=term_id, routine_position=routine_position,
                question_facing=0))
            # if the question is currently not showing redirect to this fucntion
            # except make the question show
            else:
                return redirect(url_for("learn.flashcard", deck_id=deck_id,
                routine_id=routine_id, term_id=term_id, routine_position=routine_position,
                question_facing=1))
            
        if "next" in request.form:
            return redirect_to_next(deck_id, routine_id, term_id, routine_position)

    # if the question is facing, display it, otherwise display answer
    if question_facing == 1:
        facing_up = term["question"]
    else:
        facing_up = term["answer"]

    return render_template("learn/flashcard.html", display=facing_up)