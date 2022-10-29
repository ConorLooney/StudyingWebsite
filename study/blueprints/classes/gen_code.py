from flask import render_template, request, redirect, url_for, g, flash
from study.auth import login_required
from study.db import get_db
from study.utility.helper import gen_random_code

from .main import bp
from .view_levels import admin_level_view

@bp.route("/gen_code/<class_id>", methods=("GET", "POST"))
@login_required
@admin_level_view
def gen_code(class_id):
    db = get_db()
    code = db.execute(
        "SELECT * FROM invite_code WHERE class_id = ?",
        (str(class_id),)
    ).fetchone()

    if request.method == "POST":
        if "gen_code" in request.form:
            if code is not None: # code already exists
                error = "Error: Code is already generated"
                flash(error)
                return redirect(url_for("class.gen_code", class_id=class_id))
            else:
                # function to recursively call itself until a valid new code is found
                # code only valid if it is unique 
                def make_new_code():
                    try:
                        new_code = gen_random_code(length=8)
                        db.execute(
                                "INSERT INTO invite_code (code, class_id) VALUES (?, ?)",
                                (str(new_code), str(class_id),)
                            )
                        db.commit()
                        return new_code
                    except db.IntegrityError:
                        return make_new_code()
                new_code = make_new_code()
                code = db.execute(
                    "SELECT * FROM invite_code WHERE code = ?",
                    (str(new_code),)
                ).fetchone()
        if "delete_code" in request.form:
            if code is None:
                error = "Error: No code to delete"
                flash(error)
            else:
                db.execute(
                    "DELETE FROM invite_code WHERE code = ?",
                    (str(code["code"]),)
                )
                db.commit()
                code = None

    return render_template("class/gen_code.html", code=code)