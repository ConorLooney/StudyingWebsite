from flask import request, redirect, url_for, render_template, flash, g, session
from study.auth import login_required, member_routine_view, member_deck_view
from study.db import get_db, to_bit

from .main import bp
from study.validation import presence_check

def read_form():
    return request.form["answer"]

def is_answer_correct(given_answer, term):
    return given_answer.strip() == term["answer"].strip()

def get_term(term_id):
    db = get_db()
    term = db.execute(
        "SELECT * FROM term WHERE id = ?",
        (str(term_id),)
    ).fetchone()
    return term

def record_attempt(step, term_id, is_correct):
    db = get_db()
    db.execute(
        "INSERT INTO attempt (step, term_id, user_id, is_correct) VALUES (?, ?, ?, ?)",
        (step, str(term_id), str(g.user["id"]), str(to_bit(is_correct)),)
    )
    db.commit()

def queue_to_correct(term_id, given_answer):
    session['to_correct'].append([term_id, given_answer])
    session.modified = True

@bp.route("/<deck_id>/<routine_id>/<term_id>/<routine_position>/ask", methods=("GET", "POST"))
@login_required
@member_deck_view
@member_routine_view
def ask(deck_id, routine_id, term_id, routine_position):

    term = get_term(term_id)

    if request.method == "POST":
        given_answer = read_form()

        if not presence_check(given_answer):
            error = "Error: No answer given"
            flash(error)
        else:
            is_correct = is_answer_correct(given_answer, term)
            record_attempt("a", term_id, is_correct)
            if not is_correct:
                queue_to_correct(term_id, given_answer)

            routine_position = int(routine_position) + 1
            return redirect(url_for("learn.learn", deck_id=deck_id, routine_id=routine_id,
            term_id=term_id, routine_position=routine_position))

    question = term["question"]
    return render_template("learn/ask.html", question=question)