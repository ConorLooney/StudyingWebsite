from flask import render_template
from study.auth import login_required, member_routine_view

from .utility import get_routine
from .main import bp

@bp.route("/view/<routine_id>")
@login_required
@member_routine_view
def see_one(routine_id):
    routine = get_routine(routine_id)

    return render_template("routines/see_one.html", routine=routine)