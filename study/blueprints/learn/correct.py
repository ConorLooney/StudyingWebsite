from flask import request, redirect, url_for, session, render_template, flash, g
from study.auth import login_required, member_routine_view, member_deck_view
from study.db import get_db, to_bit

from .main import bp

def pop_queue_to_correct():
    session['to_correct'].remove(session['to_correct'][0])
    session.modified = True

@bp.route("/<deck_id>/<routine_id>/<term_id>/<routine_position>/correct", methods=("GET", "POST"))
@login_required
@member_deck_view
@member_routine_view
def correct(deck_id, routine_id, term_id, routine_position):
    to_correct_queue = session['to_correct']
    first = to_correct_queue[0]
    term_id = first[0]
    to_correct_answer = first[1]

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
            pop_queue_to_correct()
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
     to_correct_answer=to_correct_answer, actual_answer=term["answer"])