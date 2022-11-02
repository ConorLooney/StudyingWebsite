from flask import request, url_for, render_template, redirect, g
from study.utility.general import get_all_user_controlled_classes, get_saved_info, get_all_user_routines, save_routine_to_class
from study.search_utility import handle_search,apply_filter
from study.auth import login_required

from .main import bp

@bp.route("/", methods=("GET", "POST"))
@login_required
def all_user():
    search_term = None
    search_function = None

    if request.method == "POST":
        if "search" in request.form:
            search_term, search_function = handle_search(request.form)

    routines = get_all_user_routines(g.user["id"])
    routines = apply_filter(routines, "title", search_term, filter_function=search_function)

    saved_info = get_saved_info(routines, "routine", g.user["id"])

    return render_template("routines/all_user.html",
     routines=routines, saved_info=saved_info)