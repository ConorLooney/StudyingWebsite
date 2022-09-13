from flask import (
    Blueprint, request, url_for, render_template, redirect, flash, g
)
from werkzeug.security import check_password_hash
from study.db import get_db, to_bit
from study.db_utility import (
    get_all_user_controlled_classes, get_saved_info, get_all_user_routines,
    save_routine_to_user, unsave_routine_from_user, save_routine_to_class
)
from study.search_utility import handle_search,apply_filter
from study.auth import login_required, private_routine_view, protected_routine_view

bp = Blueprint("routines", __name__, url_prefix="/routine")

@bp.route("/", methods=("GET", "POST"))
@login_required
def all_user():
    search_term = None
    search_function = None

    if request.method == "POST":
        if "delete_routine" in request.form:
            routine_id = request.form['routine_id']
            return redirect(url_for("routines.delete", routine_id=routine_id))
        if "update_routine" in request.form:
            routine_id = request.form['routine_id']
            return redirect(url_for("routines.update", routine_id=routine_id))    
        if "unsave_routine" in request.form:
            routine_id = request.form["routine_id"]
            unsave_routine_from_user(g.user["id"], routine_id)
        if "save_routine_to_class" in request.form:
            routine_id = request.form["routine_id"]
            class_id = request.form["classes"]
            save_routine_to_class(class_id, routine_id)
        if "search" in request.form:
            search_term, search_function = handle_search(request.form)

    routines = get_all_user_routines(g.user["id"])
    routines = apply_filter(routines, "title", search_term, filter_function=search_function)

    saved_info = get_saved_info(routines, "routine", g.user["id"])

    classes = get_all_user_controlled_classes(g.user["id"])

    return render_template("routines/all_user.html",
     routines=routines, saved_info=saved_info, classes=classes)

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

@bp.route("/create", methods=("GET", "POST"))
@login_required
def create():
    if request.method == "POST":
        routine_name = request.form["routine_name"]
        steps = request.form["steps"]
        is_public = request.form["is_public"] == "1"

        error = None
        if routine_name is None:
            error = "Routine name is required"
        if steps is None:
            error = "Routine steps are required"

        if error is None:
            db = get_db()
            cursor = db.cursor()
            try:

                cursor.execute(
                    "INSERT INTO routine (owner_id, title, steps, is_public) VALUES (?, ?, ?, ?)",
                    (str(g.user['id']), routine_name, steps, to_bit(is_public),)
                )
                db.commit()
                routine_id = cursor.lastrowid

                return redirect(url_for("routines.view_routine", routine_id=routine_id))
            except db.IntegrityError:
                error = "Routine name must be unique"

        flash(error) 
    
    return render_template("routines/create.html")

@bp.route("/view/<routine_id>")
@login_required
@protected_routine_view
def view_routine(routine_id):
    db = get_db()
    routine = db.execute(
        "SELECT * FROM routine WHERE id = ?",
        (str(routine_id),)
    ).fetchone()

    return render_template("routines/routine.html", routine=routine)

@bp.route("/update/<routine_id>", methods=("GET", "POST"))
@login_required
@private_routine_view
def update(routine_id):
    db = get_db()

    if request.method == "POST":
        routine_name = request.form["routine_name"]
        steps = request.form["steps"]
        is_public = request.form["is_public"] == "1"

        error = None
        if routine_name is None:
            error = "Routine name is required"
        if steps is None:
            error = "Routine steps are required"

        if error is None:
            try:

                db.execute(
                    "UPDATE routine SET title = ?, steps = ?, is_public = ? WHERE id = ?",
                    (routine_name, steps, str(to_bit(is_public)), str(routine_id),)
                )
                db.commit()

                return redirect(url_for("routines.view_routine", routine_id=routine_id))
            except db.IntegrityError:
                error = "Routine name must be unique"

        flash(error) 

    current_routine = db.execute(
        "SELECT * FROM routine WHERE id = ?",
        (str(routine_id),)
    ).fetchone()

    return render_template("routines/update.html", routine=current_routine)

@bp.route("/delete/<routine_id>", methods=("GET", "POST"))
@login_required
@private_routine_view
def delete(routine_id):
    db = get_db()
    if request.method == "POST":
        password = request.form["password"]
        
        error = None

        if password is None:
            error = "Password is required"
        
        if error is None:
            if check_password_hash(g.user["password"], password):
                db.execute(
                    "DELETE FROM routine WHERE id = ?",
                    (str(routine_id),)
                )
                db.commit()
                return redirect(url_for("routines.all_user"))
            else:
                error = "Incorrect password"
        
        flash(error)

    routine = db.execute(
        "SELECT * FROM routine WHERE id = ?",
        (str(routine_id),)
    ).fetchone()

    return render_template("routines/delete.html", routine=routine)