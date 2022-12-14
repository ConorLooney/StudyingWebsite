from flask import request, render_template, g
from study.utility.general import get_saved_info
from study.search_utility import handle_search,apply_filter
from study.auth import login_required

from .utility import get_all_user_routines
from .main import bp

@bp.route("/", methods=("GET", "POST"))
@login_required
def see_all():
    search_term = None
    search_function = None

    if request.method == "POST":
        if "search" in request.form:
            search_term, search_function = handle_search(request.form)

    routines = get_all_user_routines(g.user["id"])
    routines = apply_filter(routines, "title", search_term, filter_function=search_function)

    saved_info = get_saved_info(routines, "routine", g.user["id"])

    return render_template("routines/see_all.html",
     routines=routines, saved_info=saved_info)