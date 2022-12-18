from flask import request, render_template, session
from study.auth import login_required, member_routine_view, member_deck_view

from .main import bp
from study.db import get_db
from study.validation import presence_check
from .utility import record_attempt, add_to_queue_to_correct, is_answer_correct, redirect_to_next, get_term

def read_form():
    return request.form["answer"]

def get_categories(deck_id):
    db = get_db()
    terms = db.execute(
        "SELECT * FROM term WHERE deck_id = ?",
        (str(deck_id),)
    ).fetchall()

    categories = []
    for term in terms:
        if term["answer"] not in categories:
            categories.append(term["answer"])
    
    return categories

def get_questions(deck_id):
    db = get_db()
    terms = db.execute(
        "SELECT * FROM term WHERE deck_id = ?",
        (str(deck_id),)
    ).fetchall()

    questions = []
    for term in terms:
        questions.append(term["question"])
    
    return questions

def get_terms(deck_id):
    db = get_db()
    terms = db.execute(
        "SELECT * FROM term WHERE deck_id = ?",
        (str(deck_id),)
    ).fetchall()
    return terms

def get_data_from_bytes(bytes):
    # bytes[1:] to remove 'b' prefix
    # .replace("'", "") to remove enclosing ''
    # split by , to return as list
    return bytes[1:].replace("'", "").split(",")

def remove_term_from_unanswered(term_id):
    sort_data = session["sort_data"]
    unsorted = sort_data["unsorted"]

    unsorted.remove(term_id)

    sort_data["unsorted"] = unsorted
    session["sort_data"] = sort_data

def add_term_to_category(term_id, category):
    sort_data = session["sort_data"]
    categorised = sort_data[category]

    categorised.append(term_id)

    sort_data[category] = categorised
    session["sort_data"] = sort_data

def sort_term(term_id, category):
    remove_term_from_unanswered(term_id)
    add_term_to_category(term_id, category)

def get_term(term_id):
    db = get_db()
    return db.execute(
        "SELECT * FROM term WHERE id = ?",
        (str(term_id),)
    ).fetchone()

def get_unsorted_terms():
    unsorted_ids = session["sort_data"]["unsorted"]
    terms = []
    for id in unsorted_ids:
        terms.append(get_term(int(id)))
    return terms

def get_terms_in_category(category):
    category_ids = session["sort_data"][category]
    terms = []
    for id in category_ids:
        terms.append(get_term(int(id)))
    return terms

def move_term(term_id, from_category, to_category):
    sort_data = session["sort_data"]

    if from_category == "":
        from_category = "unsorted"
    if to_category == "":
        to_category = "unsorted"

    from_category_ids = sort_data[from_category]
    from_category_ids.remove(term_id)
    sort_data[from_category] = from_category_ids

    to_category_ids = sort_data[to_category]
    to_category_ids.append(term_id)
    sort_data[to_category] = to_category_ids

    session["sort_data"] = sort_data

@bp.route("/<deck_id>/<routine_id>/<term_id>/<routine_position>/sort", methods=("GET", "POST"))
@login_required
@member_deck_view
@member_routine_view
def sort(deck_id, routine_id, term_id, routine_position):
    if request.method == "POST":
        if request.headers["Content-Type"] == "application/json":
            term_id, to_category, from_category = get_data_from_bytes(str(request.data))
            
            term_id = int(term_id)
            move_term(term_id, from_category, to_category)
        else:
            # submit button pressed, process answers
            # every term in unsorted is wrong
            sort_data = session["sort_data"]

            unsorted_ids = sort_data["unsorted"]
            for term_id in unsorted_ids:
                record_attempt("s", term_id, False)

            # for every term in a category, check if category == term's answer
            categories = get_categories(deck_id)
            for category in categories:
                category_ids = sort_data[category]
                for term_id in category_ids:
                    term = get_term(term_id)
                    is_correct = term["answer"] == category
                    record_attempt("s", term_id, is_correct)

            return redirect_to_next(deck_id, routine_id, term_id, routine_position)

    elif request.method == "GET":
        session["sort_data"] = {
            "unsorted": [],
        }
        categories = get_categories(deck_id)
        for category in categories:
            session["sort_data"][category] = []
        
        terms = get_terms(deck_id)
        for term in terms:
            session["sort_data"]["unsorted"].append(term["id"])

    categories = get_categories(deck_id)
    terms = get_terms(deck_id)

    unsorted_terms = get_unsorted_terms()
    categorised_terms = {}
    for category in categories:
        terms = get_terms_in_category(category)
        categorised_terms[category] = terms

    return render_template("learn/sort.html", unsorted_terms=unsorted_terms,
    categories=categories, categorised_terms=categorised_terms)