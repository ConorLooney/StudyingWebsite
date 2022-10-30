from flask import request, redirect, url_for, render_template, g, session
from study.auth import login_required, member_routine_view, member_deck_view
from study.db import get_db, to_bit
import random

from .main import bp

def queue_to_correct(term_id, given_answer):
    session['to_correct'].append([term_id, given_answer])
    session.modified = True

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
        if not is_correct:
            queue_to_correct(term_id, chosen_answer)
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