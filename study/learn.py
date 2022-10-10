from flask import (
    Blueprint, request, redirect, url_for, session, render_template, flash, g
)
from study.auth import (
    login_required,
    member_routine_view, member_deck_view
)
from study.db import get_db, to_bit
import random

bp = Blueprint("learn", __name__, url_prefix="/learn")

def record_study_session(routine_id, deck_id):
    db = get_db()
    user_id = g.user["id"]
    db.execute(
        "INSERT INTO study_session (user_id, routine_id, deck_id) VALUES (?, ?, ?)",
        (str(user_id), str(routine_id), str(deck_id),)
    )
    db.commit()

@bp.route("/<deck_id>/<routine_id>")
@login_required
@member_deck_view
@member_routine_view
def begin_learn(deck_id, routine_id):
    db = get_db()
    terms = db.execute(
        "SELECT id FROM term WHERE deck_id = ?",
        (str(deck_id),)
    ).fetchall()
    smallest_id = terms[0]['id']

    routine_position = 0

    return redirect(url_for("learn.learn", deck_id=deck_id, routine_id=routine_id,
     term_id=smallest_id, routine_position=routine_position))

@bp.route("/<deck_id>/<routine_id>/<term_id>/<routine_position>", methods=("GET", "POST"))
@login_required
@member_deck_view
@member_routine_view
def learn(deck_id, routine_id, term_id, routine_position):
    routine_position = int(routine_position)

    db = get_db()
    steps = db.execute(
        "SELECT steps FROM routine WHERE id = ?",
        (str(routine_id),)
    ).fetchone()['steps']
    
    amount_of_steps = len(steps)
    if routine_position >= amount_of_steps:
        term_id = int(term_id)
        terms = db.execute(
            "SELECT id FROM term WHERE deck_id = ? ORDER BY id",
            (str(deck_id),)
        ).fetchall()

        if term_id == terms[len(terms)-1]["id"]:
            record_study_session(routine_id, deck_id)
            return redirect(url_for("/index"))
        else:
            for i in range(len(terms)):
                if terms[i]["id"] == term_id:
                    next_term_id = terms[i + 1]["id"]
            return redirect(url_for("learn.learn", deck_id=deck_id, routine_id=routine_id,
         term_id=next_term_id, routine_position=0))

    current_step = steps[routine_position]
    step_views = {"a": "learn.ask", "c": "learn.correct", "f": "learn.flashcard",
    "m": "learn.choice"}
    if current_step in step_views:
        return redirect(url_for(step_views[current_step], deck_id=deck_id, routine_id=routine_id,
         term_id=term_id, routine_position=routine_position))

    return redirect(url_for("/index"))

@bp.route("/<deck_id>/<routine_id>/<term_id>/<routine_position>/ask", methods=("GET", "POST"))
@login_required
@member_deck_view
@member_routine_view
def ask(deck_id, routine_id, term_id, routine_position):
    db = get_db()

    term = db.execute(
        "SELECT * FROM term WHERE id = ?",
        (str(term_id),)
    ).fetchone()

    if request.method == "POST":
        given_answer = request.form['answer']

        error = None

        if given_answer is None:
            error = "You must give an answer"
        
        if error is None:
            db = get_db()

            is_correct =  given_answer.strip() == term["answer"].strip()
            db.execute(
                "INSERT INTO attempt (step, term_id, user_id, is_correct) VALUES (?, ?, ?, ?)",
                ("a", str(term_id), str(g.user["id"]), str(to_bit(is_correct)),)
            )
            db.commit()

            session['given_answer'] = given_answer
            routine_position = int(routine_position) + 1
            return redirect(url_for("learn.learn", deck_id=deck_id, routine_id=routine_id,
            term_id=term_id, routine_position=routine_position))

        flash(error)

    return render_template("learn/ask.html", question=term["question"])

@bp.route("/<deck_id>/<routine_id>/<term_id>/<routine_position>/correct", methods=("GET", "POST"))
@login_required
@member_deck_view
@member_routine_view
def correct(deck_id, routine_id, term_id, routine_position):
    db = get_db()
    term = db.execute(
        "SELECT * FROM term WHERE id = ?",
        (str(term_id),)
    ).fetchone()

    if request.method == "POST":
        given_answer = request.form["answer"]
        error = None

        if given_answer is None:
            error = "Answer is required"

        if error is None:
            session['given_answer'] = given_answer
        else:
            flash(error)

        is_correct = term["answer"].strip() == given_answer.strip()
        db.execute(
            "INSERT INTO attempt (step, term_id, user_id, is_correct) VALUES (?, ?, ?, ?)",
            ("c", str(term_id), str(g.user["id"]), str(to_bit(is_correct)),)
        )
        db.commit()

    given_answer = session['given_answer']

    if term["answer"].strip() == given_answer.strip():
        session.pop("given_answer", None)
        routine_position = int(routine_position) + 1
        return redirect(url_for("learn.learn", deck_id=deck_id, routine_id=routine_id,
         term_id=term_id, routine_position=routine_position))

    return render_template("learn/correct.html", question=term["question"],
     given_answer=given_answer, actual_answer=term["answer"])

@bp.route("/<deck_id>/<routine_id>/<term_id>/<routine_position>/flashcard", methods=("GET", "POST"))
@login_required
@member_deck_view
@member_routine_view
def flashcard(deck_id, routine_id, term_id, routine_position):
    db = get_db()
    term = db.execute(
        "SELECT * FROM term WHERE id = ?",
        (str(term_id),)
    ).fetchone()

    if "flashcard_display" not in session:
        session["flashcard_display"] = term["question"]

    if request.method == "POST":
        # Update attempts 
        db.execute(
            "INSERT INTO attempt (step, term_id, user_id, is_correct) VALUES (?, ?, ?, ?)",
            ("f", str(term_id), str(g.user["id"]), str(to_bit(1)),)
        )
        db.commit()

        if "flip" in request.form:
            if session["flashcard_display"] == term["question"]:
                session["flashcard_display"] = term["answer"]
            else:
                session["flashcard_display"] = term["question"]
            return render_template("learn/flashcard.html", display=session["flashcard_display"])
        if "next" in request.form:
            session.pop("flashcard_display", None)
            routine_position = int(routine_position) + 1
            return redirect(url_for("learn.learn", deck_id=deck_id, routine_id=routine_id, 
             term_id=term_id, routine_position=routine_position))

    return render_template("learn/flashcard.html", display=session["flashcard_display"])

@bp.route("/<deck_id>/<routine_id>/<term_id>/<routine_position>/choice", methods=("GET", "POST"))
@login_required
@member_deck_view
@member_routine_view
def choice(deck_id, routine_id, term_id, routine_position):
    """Presents question with choice of up to 4 answers.
    Incorrect answers are randomly selected from other terms
    if there are less than 4 terms as many answers are
    retrieved as possible in a random order"""
    db = get_db()
    current_term = db.execute(
        "SELECT * FROM term WHERE id = ?",
        (str(term_id),)
    ).fetchone()

    if request.method == "POST":
        chosen_answer = request.form["answer"].replace("\r", "")
        is_correct = chosen_answer.strip() == current_term["answer"].strip()
        db.execute(
            "INSERT INTO attempt (step, term_id, user_id, is_correct) VALUES (?, ?, ?, ?)",
            ("m", str(term_id), str(g.user["id"]), str(to_bit(is_correct)),)
        )
        db.commit()
        session['given_answer'] = chosen_answer
        routine_position = int(routine_position) + 1
        return redirect(url_for("learn.learn", deck_id=deck_id, routine_id=routine_id,
            term_id=term_id, routine_position=routine_position))

    all_terms = db.execute(
        "SELECT * FROM term WHERE deck_id = ?",
        (str(deck_id),)
    ).fetchall()
    all_terms.remove(current_term)
    random.shuffle(all_terms)

    choices = []

    if len(all_terms) > 3:
        choices = all_terms[0:4]
    elif len(all_terms) > 0:
        choices = all_terms
    else:
        choices = [current_term]
    
    choices[random.randint(0, min(len(choices), len(all_terms))) - 1] = current_term

    return render_template("learn/choice.html", correct_term=current_term, choices=choices)