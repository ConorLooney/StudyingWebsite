from flask import render_template, request, redirect, url_for, g
from study.auth import login_required
from study.db import get_db
from study.search_utility import apply_filter, handle_search
from study.utility.general import remove_user_from_class, get_saved_info

from .main import bp

@bp.route("/all_user", methods=("GET", "POST"))
@login_required
def all_user():
    db = get_db()
    search_term = None
    search_function = None
    if request.method == "POST":
        if "update_class" in request.form:
            class_id = request.form["class_id"]
            return redirect(url_for("class.update", class_id=class_id))
        if "delete_class" in request.form:
            class_id = request.form["class_id"]
            return redirect(url_for("class.delete", class_id=class_id))
        if "leave_class" in request.form:
            class_id = request.form["class_id"]
            user_id = g.user["id"]
            remove_user_from_class(user_id, class_id)
        if "search" in request.form:
            search_term, search_function = handle_search(request.form)
    
    classes = db.execute(
        "SELECT * FROM class \
        JOIN user_class ON class.id = user_class.class_id \
        WHERE user_class.user_id = ?",
        (str(g.user["id"]),)
    ).fetchall()
    classes = apply_filter(classes, "title", search_term, filter_function=search_function)
    saved_info = get_saved_info(classes, "class", g.user["id"])

    return render_template("class/all_user.html", classes=classes, saved_info=saved_info)