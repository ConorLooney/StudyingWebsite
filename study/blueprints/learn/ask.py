from flask import request, redirect, url_for, render_template, flash, g
from study.auth import login_required, member_routine_view, member_deck_view
from study.db import get_db, to_bit

from .main import bp

def queue_to_correct(term_id, given_answer):
    session['to_correct'].append([term_id, given_answer])
    session.modified = True

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
            if not is_correct:
                queue_to_correct(term_id, given_answer)

            routine_position = int(routine_position) + 1
            return redirect(url_for("learn.learn", deck_id=deck_id, routine_id=routine_id,
            term_id=term_id, routine_position=routine_position))

        flash(error)

    return render_template("learn/ask.html", question=term["question"])