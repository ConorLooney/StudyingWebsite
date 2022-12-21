from flask import request, render_template, flash
from study.auth import login_required, member_routine_view, member_deck_view

from .main import bp
from study.db import get_db

def get_terms(deck_id):
    db = get_db()
    terms = db.execute(
        "SELECT * FROM term WHERE deck_id = ?",
        (str(deck_id),)
    ).fetchall()
    return terms

def get_ordinal_number_from_answer(answer):
    """Ordinal number is based on term answer e.g. 
    Q. Test A. 32 --- ordinal number = 32
    Q. Test2 A. 1 - Hi --- ordinal number = 1
    An answer with [number] -[other] will have ordinal number [other]"""
    if answer.isnumeric():
        return int(answer)
    elif " - " in answer:
        digit = answer.split(" - ")[0]
        return int(digit)
    else:
        flash("Error: This deck has terms without a defined ordinal number")
        return 1

def get_terms_ordinal_values(terms):
    """Return dict of term id key to ordinal number value"""
    ordinal_values = {}
    for term in terms:
        ordinal_values[int(term["id"])] = get_ordinal_number_from_answer(term["answer"])
    return ordinal_values

@bp.route("/<deck_id>/<routine_id>/<term_id>/<routine_position>/sort", methods=("GET", "POST"))
@login_required
@member_deck_view
@member_routine_view
def sort(deck_id, routine_id, term_id, routine_position):
    if request.method == "POST":
        if request.headers["Content-Type"] == "application/json":
            pass
        else:
            pass

    terms = get_terms(deck_id)
    ordinal_values = get_terms_ordinal_values(terms)

    return render_template("learn/order.html", )