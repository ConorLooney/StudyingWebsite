from flask import render_template, g
from study.auth import login_required, member_routine_view

from .utility import get_routine
from .main import bp

@bp.route("/view/<routine_id>")
@login_required
@member_routine_view
def see_one(routine_id):
    routine = get_routine(routine_id)
    # TODO: Add steps object and use those instead of hardcoded stuff here
    steps = []
    for step in routine["steps"]:
        if step == "a":
            steps.append("Ask")
        elif step == "c":
            steps.append("Correct")
        elif step == "m":
            steps.append("Multiple choice")
        elif step == "f":
            steps.append("Flashcards")
        elif step == "b":
            steps.append("Blanks")
        elif step == "y":
            steps.append("Copy")

    owner_id = routine["owner_id"]
    logged_in_id = g.user["id"]
    is_owner = owner_id == logged_in_id

    return render_template("routines/see_one.html", routine=routine, steps=steps,
    is_owner=is_owner)