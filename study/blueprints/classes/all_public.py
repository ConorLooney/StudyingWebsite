from flask import render_template, request, redirect, url_for, g, flash
from study.auth import login_required
from study.db import get_db
from study.search_utility import apply_filter, handle_search
from study.utility.general import remove_user_from_class

from .main import bp

@bp.route("/all_public", methods=("GET", "POST"))
@login_required
def all_public():
    db = get_db()
    search_term = None
    search_function = None
    
    if request.method == "POST":
        if "code_join_class" in request.form:
            return redirect(url_for("class.code_join"))
        if "request_to_join_class" in request.form:
            class_id = request.form["class_id"]
            try:
                db.execute(
                    "INSERT INTO join_request (requester_id, class_id) VALUES (?, ?)",
                    (str(g.user["id"]), str(class_id),)
                )
                db.commit()
            except db.IntegrityError:
                error = "Error: User has already a request to join this class"
                flash(error)
        if "leave_class" in request.form:
            class_id = request.form["class_id"]
            user_id = g.user["id"]
            remove_user_from_class(user_id, class_id)
        if "delete_class" in request.form:
            class_id = request.form["class_id"]
            return redirect(url_for("class.delete", class_id=class_id))
        if "search" in request.form:
            search_term, search_function = handle_search(request.form)
        
    classes = db.execute(
        "SELECT * FROM class WHERE is_public = ?",
        (str(int(True)),)
    ).fetchall()
    classes = apply_filter(classes, "title", search_term, filter_function=search_function)

    member_info = []
    for class_ in classes:
        if str(class_["owner_id"]) == str(g.user["id"]):
            member_info.append(1)
            continue

        membership = db.execute(
            "SELECT * FROM user_class \
            WHERE user_class.user_id = ? AND user_class.class_id = ?",
            (str(g.user["id"]), str(class_["id"]),)
        ).fetchone()

        if membership is None:
            member_info.append(-1)
        else:
            member_info.append(0)

    return render_template("class/all_public.html", classes=classes, member_info=member_info)