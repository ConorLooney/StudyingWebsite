from flask import render_template, g
from study.db import get_db

from .main import bp
from .view_levels import member_level_view

@bp.route("/meta_view/<class_id>")
@member_level_view
def meta_view(class_id):
    db = get_db()
    view_class = db.execute(
        "SELECT * FROM class WHERE id = ?",
        (str(class_id),)
    ).fetchone()

    members = db.execute(
        "SELECT * FROM user\
        JOIN user_class ON user.id=user_class.user_id\
        WHERE class_id = ?",
        (str(class_id),)
    ).fetchall()

    admins = db.execute(
        "SELECT * FROM user\
        JOIN admin_class ON user.id=admin_class.admin_id\
        WHERE class_id = ?",
        (str(class_id),)
    ).fetchall()

    owner = db.execute(
        "SELECT * FROM user WHERE id = ?",
        (str(view_class["owner_id"]),)
    ).fetchone()

    user = g.user

    return render_template("class/meta_view.html", view_class=view_class,
     owner=owner, members=members, admins=admins, user=user)