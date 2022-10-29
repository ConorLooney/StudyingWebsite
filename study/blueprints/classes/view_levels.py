import functools
from flask import redirect, url_for, g

def member_level_view(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            return redirect(url_for("auth.login"))

        class_id = kwargs['class_id']
        db = get_db()
        current_class = db.execute(
            "SELECT * FROM class WHERE id = ?",
            (str(class_id),)
        ).fetchone()

        if current_class is None:
            return redirect(url_for("/index"))

        authorised_ids = [current_class['owner_id']]
        authorised_ids.extend([row["user_id"] for row in db.execute(
            "SELECT user_id FROM user_class WHERE class_id = ?",
            (str(class_id),)
        ).fetchall()])
        if g.user['id'] not in authorised_ids:
            return redirect(url_for("/index"))

        return view(**kwargs)
    
    return wrapped_view

def admin_level_view(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            return redirect(url_for("auth.login"))

        class_id = kwargs['class_id']
        db = get_db()
        current_class = db.execute(
            "SELECT * FROM class WHERE id = ?",
            (str(class_id),)
        ).fetchone()

        if current_class is None:
            return redirect(url_for("/index"))

        authorised_ids = [current_class['owner_id']]
        authorised_ids.extend([row["admin_id"] for row in db.execute(
            "SELECT admin_id FROM admin_class WHERE class_id = ?",
            (str(class_id),)
        ).fetchall()])
        if g.user['id'] not in authorised_ids:
            return redirect(url_for("/index"))

        return view(**kwargs)
    
    return wrapped_view

def owner_level_view(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            return redirect(url_for("auth.login"))

        class_id = kwargs['class_id']
        db = get_db()
        current_class = db.execute(
            "SELECT * FROM class WHERE id = ?",
            (str(class_id),)
        ).fetchone()

        if current_class is None:
            return redirect(url_for("/index"))

        if g.user['id'] == current_class["owner_id"]:
            return view(**kwargs)
        else:
            return redirect(url_for("/index"))
    
    return wrapped_view