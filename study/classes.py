import functools
from flask import (
    Blueprint, render_template, request, redirect, url_for, g, flash
)
from werkzeug.security import check_password_hash
from study.auth import login_required
from study.db import get_db, to_bit
from study.utility.helper import gen_random_code
from study.search_utility import apply_filter, handle_search
from study.utility.general import (
    save_deck_to_user, save_routine_to_user, remove_user_from_class, get_all_user_routines,
    add_user_to_class, delete_class, get_saved_info
)
import time

bp = Blueprint("class", __name__, url_prefix="/class")

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

"""Page for user to create a new class

User must be logged in
Takes class name, description and is public or private


Inserts new class row in class table
Inserts new mebership in user_class table"""
@bp.route("/create", methods=("GET", "POST"))
@login_required
def create():
    if request.method == "POST":
        title = request.form["title"]
        description = request.form["description"]
        is_public = request.form["is_public"] == "public"

        error = None

        if title is None:
            error = "Error: Class name is required"

        if error is None:
            db = get_db()
            cursor = db.cursor()
            cursor.execute(
                "INSERT INTO class (owner_id, title, description, is_public) VALUES (?, ?, ?, ?)",
                (str(g.user["id"]), str(title), str(description), to_bit(is_public),)
            )
            db.commit()
            class_id = cursor.lastrowid
            cursor = db.cursor()
            try:
                cursor.execute(
                    "INSERT INTO user_class (user_id, class_id) VALUES (?, ?)",
                    (str(g.user["id"]), str(class_id),)
                )
                db.commit()
                return redirect(url_for("class.view", class_id=class_id))
            except db.IntegrityError:
                error = "Error: User already member of this class"


        flash(error)
    return render_template("class/create.html")

"""Page for user to view class properties, decks, routines and modify membership

User must be logged in
User must be a member of the class

User can select a deck to study with a routine
Routines avaliable are routines saved to the class, routines saved by the user,
or routines owned by the user
If owner or admin of class, user can add and remove admins
If owner or admin of class, user can generate code to join class
If owner of admin of class, use can accept and reject join requests
If owner of admin of class, user can remove decks and routines
"""
@bp.route("/view/<class_id>", methods=("GET", "POST"))
@login_required
@member_level_view
def view(class_id):
    db = get_db()
    if request.method == "POST":
        error = None
        if "study_deck" in request.form:
            deck_id = request.form["deck_id"]
            routine_id = request.form["routines"]
            return redirect(url_for("learn.begin_learn", deck_id=deck_id, routine_id=routine_id))

        if "unsave_deck_from_class" in request.form:
            deck_id = request.form["deck_id"]
            db.execute(
                "DELETE FROM deck_class WHERE deck_id = ?",
                (str(deck_id),)
            )
            db.commit()

        if "unsave_routine_from_class" in request.form:
            routine_id = request.form["routine_id"]
            db.execute(
                "DELETE FROM routine_class WHERE routine_id = ?",
                (str(routine_id),)
            )
            db.commit()
        
        if "save_deck_to_user" in request.form:
            deck_id = request.form["deck_id"]
            save_deck_to_user(g.user["id"], deck_id)

        if "unsave_deck_from_user" in request.form:
            deck_id = request.form["deck_id"]
            db.execute(
                "DELETE FROM save_deck WHERE deck_id = ? AND user_id = ?",
                (str(deck_id), str(g.user["id"]),)
            )
            db.commit()

        if "save_routine_to_user" in request.form:
            print(request.form)
            routine_id = request.form["routine_id"]
            save_routine_to_user(g.user["id"], routine_id)

        if "unsave_routine_from_user" in request.form:
            routine_id = request.form["routine_id"]
            db.execute(
                "DELETE FROM save_routine WHERE routine_id = ? AND user_id = ?",
                (str(routine_id), str(g.user["id"]),)
            )
            db.commit()

        if error is not None:
            flash(error)

    view_class = db.execute(
        "SELECT * FROM class WHERE id = ?",
        (str(class_id),)
    ).fetchone()

    decks = db.execute(
        "SELECT * FROM deck \
        JOIN deck_class ON deck_class.deck_id = deck.id \
        WHERE deck_class.class_id = ?",
        (str(class_id),)
    ).fetchall()

    class_routines = db.execute(
        "SELECT * FROM routine \
        JOIN routine_class ON routine_class.routine_id = routine.id \
        WHERE routine_class.class_id = ?",
        (str(class_id),)
    ).fetchall()
    user_routines = get_all_user_routines(g.user["id"])

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

    saved_decks_info = []
    for deck in decks:
        if str(deck["owner_id"]) == str(g.user["id"]):
            saved_decks_info.append(-1) # cannot be saved
            continue

        save_deck = db.execute(
            "SELECT * FROM save_deck WHERE deck_id = ? AND user_id = ?",
            (str(deck["id"]), str(g.user["id"]),)
        ).fetchall()

        if len(save_deck) > 0:
            saved_decks_info.append(1) # already saved, should be unsaved
        else:
            saved_decks_info.append(0) # can be saved

    saved_routines_info = []
    for routine in class_routines:
        if str(routine["owner_id"]) == str(g.user["id"]):
            saved_routines_info.append(-1) # cannot be saved
            continue

        save_routine = db.execute(
            "SELECT * FROM save_routine WHERE routine_id = ? AND user_id = ?",
            (str(routine["id"]), str(g.user["id"]),)
        ).fetchall()

        if len(save_routine) > 0:
            saved_routines_info.append(1) # already saved, should be unsaved
        else:
            saved_routines_info.append(0) # can be saved

    user = g.user
    
    return render_template("class/view.html",
     user=user, view_class=view_class, owner=owner, saved_decks_info=saved_decks_info, decks=decks,
      saved_routines_info=saved_routines_info, class_routines=class_routines, user_routines=user_routines,
      admins=admins)

"""Page for adding and removing class mebers, admins, decks, and routines

Only allowed to view if you own a class or you are an admin

Sees list of class members
Can remove member
Sees list of class admins
Can unadmin admin
Sees list of join requests
Can accept or reject request
Can generate join code
Can see list of decks and unsave them from class
Can see list of routines and unsave them from class"""
@bp.route("/admin_view/<class_id>", methods=("GET", "POST"))
@admin_level_view
def admin_view(class_id):
    db = get_db()
    if request.method == "POST":
        error = None

        if "gen_code" in request.form:
            return redirect(url_for("class.gen_code", class_id=class_id))
        if "remove_user" in request.form:
            user_id = request.form["user_id"]
            remove_user_from_class(user_id, class_id)
        if "make_admin" in request.form:
            try:
                user_id = request.form["user_id"]
                db.execute(
                    "INSERT INTO admin_class (admin_id, class_id) VALUES (?, ?)",
                    (str(user_id), str(class_id),)
                )
                db.commit()
            except db.IntegrityError:
                error = "Error: User is already admin of this class"
        if "remove_admin" in request.form:
            user_id = request.form["user_id"]
            db.execute(
                "DELETE FROM admin_class WHERE admin_id = ?",
                (str(user_id),)
            )
            db.commit()
        if "reject_request" in request.form:
            user_id = request.form["user_id"]
            db.execute(
                "DELETE FROM join_request WHERE requester_id = ? AND class_id = ?",
                (str(user_id), str(class_id),)
            )
            db.commit()
        if "accept_request" in request.form:
            user_id = request.form["user_id"]
            try:
                db.execute(
                    "INSERT INTO user_class (user_id, class_id) VALUES (?, ?)",
                    (str(user_id), str(class_id),)
                )
                db.commit()
            except db.IntegrityError:
                error = "Error: User already member of this class"
            db.execute(
                "DELETE FROM join_request WHERE requester_id = ? AND class_id = ?",
                (str(user_id), str(class_id),)
            )
            db.commit()
        if "unsave_deck" in request.form:
            deck_id = request.form["deck_id"]
            db.execute(
                "DELETE FROM deck_class WHERE deck_id = ? AND class_id = ?",
                (str(deck_id), str(class_id),)
            )
            db.commit()
        if "unsave_routine_from_class" in request.form:
            routine_id = request.form["routine_id"]
            db.execute(
                "DELETE FROM routine_class WHERE routine_id = ? AND class_id = ?",
                (str(routine_id), str(class_id),)
            )
            db.commit()
        
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

    decks = db.execute(
        "SELECT * FROM deck \
        JOIN deck_class ON deck_class.deck_id = deck.id \
        WHERE deck_class.class_id = ?",
        (str(class_id),)
    ).fetchall()

    class_routines = db.execute(
        "SELECT * FROM routine \
        JOIN routine_class ON routine_class.routine_id = routine.id \
        WHERE routine_class.class_id = ?",
        (str(class_id),)
    ).fetchall()
    user_routines = get_all_user_routines(g.user["id"])

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

    join_requests = db.execute(
        "SELECT * FROM user\
        JOIN join_request ON user.id=join_request.requester_id\
        WHERE class_id = ?",
        (str(class_id),)
    ).fetchall()

    user = g.user

    is_owner = str(owner["id"]) == str(g.user["id"])
    is_admin =  str(g.user["id"]) in [str(x["id"]) for x in admins]

    return render_template("class/admin_view.html", user=user, view_class=view_class, owner=owner, decks=decks,
      class_routines=class_routines, user_routines=user_routines, members=members,
      admins=admins, is_owner=is_owner, is_admin=is_admin, join_requests=join_requests)

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
        (str(to_bit(True)),)
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

@bp.route("/delete/<class_id>", methods=("GET", "POST"))
@login_required
@owner_level_view
def delete(class_id):
    db = get_db()
    if request.method == "POST":
        password = request.form["password"]

        error = None

        if password is None:
            error = "Error: Password is required"

        if check_password_hash(g.user["password"], password):
            delete_class(class_id)
            return redirect(url_for("/index"))
        else:
            error = "Incorrect password"

        flash(error)
    
    class_ = db.execute(
        "SELECT * FROM class WHERE id = ?",
        (str(class_id),)
    ).fetchone()

    return render_template("class/delete.html", class_=class_)

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
