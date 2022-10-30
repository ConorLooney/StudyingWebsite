from flask import request, render_template, g
from study.db import get_db, to_bit
from study.utility.general import get_all_user_controlled_classes, get_saved_info, save_routine_to_user, unsave_routine_from_user, save_routine_to_class
from study.search_utility import handle_search,apply_filter
from study.auth import login_required

from .main import bp

@bp.route("/all_public", methods=("GET", "POST"))
@login_required
def all_public():
    db = get_db()
    search_term = None
    search_function = None

    if request.method == "POST":
        if "save_routine" in request.form:
            routine_id = request.form["routine_id"]
            save_routine_to_user(g.user["id"], routine_id)
        if "unsave_routine" in request.form:
            routine_id = request.form["routine_id"]
            unsave_routine_from_user(g.user["id"], routine_id)
        if "save_routine_to_class" in request.form:
            routine_id = request.form["routine_id"]
            class_id = request.form["classes"]
            save_routine_to_class(class_id, routine_id)
        if "search" in request.form:
            search_term, search_function = handle_search(request.form)

    routines = db.execute(
    "SELECT * FROM routine WHERE is_public = ?",
    (to_bit(True),)
    ).fetchall()
    routines = apply_filter(routines, "title", search_term, filter_function=search_function)
    saved_info = get_saved_info(routines, "routine", g.user["id"])
        
    classes = get_all_user_controlled_classes(g.user["id"])

    return render_template("routines/all_public.html",
     routines=routines, saved_info=saved_info, classes=classes)