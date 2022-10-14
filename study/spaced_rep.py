from flask import (
    Blueprint, render_template, g, request, redirect, url_for
)
from study.auth import login_required
from study.db import get_db
import datetime

bp = Blueprint("spaced_repetition", __name__, url_prefix="/spaced_repetition")

def find_next_study_date(previous_dates):
    print(previous_dates)
    if len(previous_dates) == 0:
        return datetime.date.today()
    elif len(previous_dates) == 1:
        previous_date = previous_dates[0]
        return previous_date + datetime.timedelta(days=1)
    else:
        previous_date = previous_dates[len(previous_dates)-1]
        previous_previous_date = previous_dates[len(previous_dates)-2]
        time_between = previous_date - previous_previous_date
        return previous_date + datetime.timedelta(days=time_between.days)

@bp.route("/list", methods=("GET", "POST"))
@login_required
def list():
    if request.method == "POST":
        if "study" in request.form:
            deck_id = request.form["deck_id"]
            routine_id = request.form["routine_id"]
            return redirect(url_for("learn.begin_learn", deck_id=deck_id, routine_id=routine_id))
        elif "unsave_from_spaced_repetition":
            deck_id = request.form["deck_id"]
            routine_id = request.form["routine_id"]
            db = get_db()
            db.execute(
                "DELETE FROM spaced_repetition_setting WHERE \
                user_id = ? AND deck_id = ? AND routine_id = ?",
                (str(g.user["id"]), str(deck_id), str(routine_id),)
            )
            db.commit()
    db = get_db()
    user_id = g.user["id"]
    deck_routine_pairs = db.execute(
        "SELECT * FROM spaced_repetition_setting WHERE user_id = ?",
        (str(user_id),)
    ).fetchall()
    suggestions = []
    decks = []
    routines = []
    for pair in deck_routine_pairs:
        study_sessions = db.execute(
            "SELECT unixepoch(date_studied) FROM study_session \
            WHERE user_id = ? AND deck_id = ? AND routine_id = ?\
            ORDER BY unixepoch(date_studied)",
            (str(user_id), str(pair["deck_id"]), str(pair["routine_id"]),)
        ).fetchall()
        dates = []
        for session in study_sessions:
            date = datetime.date.fromtimestamp(session["unixepoch(date_studied)"])
            dates.append(date)
        next_date = find_next_study_date(dates)
        print("Next date:")
        print(next_date)
        if next_date == datetime.date.today():
            suggestions.append(pair)
            deck = db.execute(
                "SELECT * FROM deck WHERE id = ?",
                str(pair["deck_id"],)
            ).fetchone()
            decks.append(deck)
            routine = db.execute(
                "SELECT * FROM routine WHERE id = ?",
                (str(pair["routine_id"]),)
            ).fetchone()
            routines.append(routine)

    default_date = datetime.datetime.today().date()

    return render_template("spaced_rep/list.html", 
    default_date=default_date, suggestions=suggestions, decks=decks, routines=routines)