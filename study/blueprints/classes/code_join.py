from flask import Blueprint, render_template, request, redirect, url_for, g, flash
from study.auth import login_required
from study.db import get_db
from study.utility.general import add_user_to_class
import time

from .main import bp

@bp.route("/code_join", methods=("GET", "POST"))
@login_required
def code_join():
    # in seconds, half an hour
    INVITE_CODE_LIFETIME = 60 * 30
    if request.method == "POST":
        code = request.form["code"]

        error = None

        if code is None:
            error = "Error: Must enter code"

        db = get_db()
        invite_code = db.execute(
            "SELECT * FROM invite_code WHERE code = ?",
            (str(code),)
        ).fetchone()

        if invite_code is None:
            error = "Error: Invalid code"

        if error is None:
            time_since_creation = time.time() - int(db.execute(
                "SELECT unixepoch(created) FROM invite_code WHERE \
                id = ?",
                (str(invite_code["id"]),)
            ).fetchone()["unixepoch(created)"])
            
            if time_since_creation > INVITE_CODE_LIFETIME:
                db.execute(
                    "DELETE FROM invite_code WHERE id = ?",
                    (str(invite_code["id"]),)
                )
                db.commit()
                error = "Error: Code has expired"
        
        if error is None:
            class_id = invite_code["class_id"]
            add_user_to_class(g.user["id"], class_id)
            return redirect(url_for("class.view", class_id=class_id))
        
        flash(error)

    return render_template("class/code_join.html")