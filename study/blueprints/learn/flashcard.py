from flask import request, redirect, url_for, session, render_template, g
from study.auth import login_required, member_routine_view, member_deck_view
from study.db import get_db, to_bit

from .main import bp

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