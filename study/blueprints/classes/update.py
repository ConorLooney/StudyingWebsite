from flask import render_template, request, redirect, url_for
from study.auth import login_required
from study.db import get_db, to_bit

from .main import bp
from .view_levels import owner_level_view

@bp.route("/update/<class_id>", methods=("GET", "POST"))
@login_required
@owner_level_view
def update(class_id):
    db = get_db()
    if request.method == "POST":
        title = request.form["title"]
        description = request.form["description"]
        is_public = request.form["is_public"] == "public"
        db.execute(
            "UPDATE class SET title = ?, description = ?, is_public = ? \
            WHERE id = ?",
            (str(title), str(description), str(to_bit(is_public)), str(class_id),)
        )
        db.commit()
        return redirect(url_for("class.view", class_id=class_id))

    class_ = db.execute(
        "SELECT * FROM class WHERE id = ?",
        (str(class_id),)
    ).fetchone()
    return render_template("class/update.html", class_=class_)