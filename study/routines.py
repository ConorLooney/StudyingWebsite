from flask import (
    Blueprint, request, url_for, render_template, redirect, flash, g
)
from werkzeug.security import check_password_hash
from study.db import get_db, to_bit
from study.auth import login_required, private_routine_view, protected_routine_view

bp = Blueprint("routines", __name__, url_prefix="/routine")

@bp.route("/", methods=("GET", "POST"))
@login_required
def all_user():
    db = get_db()
    search_term = None
    if request.method == "POST":
        if "delete_routine" in request.form:
            routine_id = request.form['routine_id']
            return redirect(url_for("routines.delete", routine_id=routine_id))
        if "update_routine" in request.form:
            routine_id = request.form['routine_id']
            return redirect(url_for("routines.update", routine_id=routine_id))    
        if "unsave_routine" in request.form:
            print("Hi")
            routine_id = request.form["routine_id"]
            print(len(db.execute("SELECT * FROM save_routine").fetchall()))
            print((str(g.user["id"]), str(routine_id),))
            db.execute(
                "DELETE FROM save_routine WHERE user_id = ? AND routine_id = ?",
                (str(g.user["id"]), str(routine_id),)
            )
            db.commit()
            print(len(db.execute("SELECT * FROM save_routine").fetchall()))
        if "search" in request.form:
            search_term = request.form["search_field"]
            search_criteria = request.form["search_criteria"]
            if search_term == "":
                search_term = None
                search_criteria = None
            if search_criteria == "equals":
                search_term = str(search_term)
            elif search_criteria == "contains":
                search_term = "%" + str(search_term) + "%"
    
    if search_term is None:
        routines = db.execute(
            "SELECT * FROM routine WHERE owner_id = ?",
            (str(g.user['id']))
        ).fetchall()
        routines.extend(db.execute(
            "SELECT * FROM routine \
            JOIN save_routine ON save_routine.routine_id = routine.id \
            WHERE save_routine.user_id = ?",
            (str(g.user["id"]),)
        ).fetchall())
    else:
        routines = db.execute(
            "SELECT * FROM routine WHERE owner_id = ? AND title LIKE ?",
            (str(g.user['id']), str(search_term),)
        ).fetchall()
        routines.extend(db.execute(
            "SELECT * FROM routine \
            JOIN save_routine ON save_routine.routine_id = routine.id \
            WHERE save_routine.user_id = ? AND routine.title LIKE ?",
            (str(g.user["id"]), str(search_term),)
        ).fetchall())

    owned_info = []
    for routine in routines:
        if str(routine["owner_id"]) == str(g.user["id"]):
            owned_info.append(True)
        else:
            owned_info.append(False)

    return render_template("routines/all_user.html", routines=routines, owned_info=owned_info)

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
            try:

                db.execute(
                    "INSERT INTO routine (owner_id, title, steps, is_public) VALUES (?, ?, ?, ?)",
                    (str(g.user['id']), routine_name, steps, to_bit(is_public),)
                )
                db.commit()

                routine_id = db.execute(
                    "SELECT * FROM routine WHERE title = ?",
                    (routine_name,)
                ).fetchone()['id']

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

@bp.route("/all_public", methods=("GET", "POST"))
@login_required
def all_public():
    db = get_db()
    search_term = None
    if request.method == "POST":
        if "save_routine" in request.form:
            print("hello")
            routine_id = request.form["routine_id"]
            db.execute(
                "INSERT INTO save_routine (user_id, routine_id) VALUES (?, ?)",
                (str(g.user["id"]), str(routine_id),)
            )
            db.commit()
        if "unsave_routine" in request.form:
            routine_id = request.form["routine_id"]
            db.execute(
                "DELETE FROM save_routine WHERE user_id = ? AND routine_id = ?",
                (str(g.user["id"]), str(routine_id),)
            )
            db.commit()
        if "search" in request.form:
            search_term = request.form["search_field"]
            search_criteria = request.form["search_criteria"]
            if search_term == "":
                search_term = None
                search_criteria = None
            if search_criteria == "equals":
                search_term = str(search_term)
            elif search_criteria == "contains":
                search_term = "%" + str(search_term) + "%"

    if search_term is None:
        routines = db.execute(
        "SELECT * FROM routine WHERE is_public = ?",
        (to_bit(True),)
        ).fetchall()
    else:
        routines = db.execute(
            "SELECT * FROM routine WHERE is_public = ? AND title LIKE ?",
            (to_bit(True), str(search_term),)
        ).fetchall()

    saved_info = []
    for routine in routines:
        print(routine["owner_id"])
        print(g.user["id"])
        if routine["owner_id"] == g.user["id"]:
            saved_info.append(-1)
            continue
            
        save_routine = db.execute(
            "SELECT * FROM save_routine WHERE routine_id = ? AND user_id = ?",
            (str(routine["id"]), str(g.user["id"]),)
        ).fetchall()
        
        if len(save_routine) > 0:
            saved_info.append(1)
        else:
            saved_info.append(0)
        
        

    return render_template("routines/all_public.html", routines=routines, saved_info=saved_info)