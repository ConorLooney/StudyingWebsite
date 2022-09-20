from flask import (
    Blueprint, render_template, g, request, flash, redirect, url_for
)
from werkzeug.security import check_password_hash
from study.utility.general import (
    save_deck_to_class, unsave_deck_from_user, save_deck_to_user, get_all_user_routines,
    get_saved_info, get_all_user_decks, get_all_user_controlled_classes
)
from study.utility.folder import (
    get_all_immediate_child_folders, new_folder, open_folder, open_prev_folder,
    move_deck_to_folder, move_saved_deck_to_folder, delete_folder, get_formatted_folder_path,
    rename_folder, move_folder_to_folder, get_user_root_folder, get_all_folders_orderered
)
from study.db import get_db, to_bit
from study.auth import login_required, owner_deck_view, member_deck_view
from study.search_utility import handle_search, apply_filter

bp = Blueprint("decks", __name__)

@login_required
@bp.route("/", methods=("GET", "POST"))
def all_user():
    search_term = None
    search_function = None
    
    if request.method == "POST":
        if "new_deck" in request.form:
            return redirect(url_for("decks.create"))
        elif "delete_deck" in request.form:
            deck_id = request.form["deck_id"]
            return redirect(url_for("decks.delete", deck_id=deck_id))
        elif "update_deck" in request.form:
            deck_id = request.form["deck_id"]
            return redirect(url_for("decks.update", deck_id=deck_id))
        elif "study_deck" in request.form:
            deck_id = request.form["deck_id"]
            routine_id = request.form["routines"]
            return redirect(url_for("learn.begin_learn", deck_id=deck_id, routine_id=routine_id))
        elif "unsave_deck" in request.form:
            deck_id = request.form["deck_id"]
            unsave_deck_from_user(g.user["id"], deck_id)
        elif "save_deck_to_class" in request.form:
            deck_id = request.form["deck_id"]
            class_id = request.form["classes"]
            save_deck_to_class(class_id, deck_id)
        elif "rename_folder" in request.form:
            folder_id = request.form["folder_id"]
            new_title = request.form["new_folder_title"]
            rename_folder(folder_id, new_title)
        elif "move_deck_to_folder" in request.form:
            deck_id = request.form["deck_id"]
            folder_id = request.form["folders"]
            if "saved_deck" in request.form:
                move_saved_deck_to_folder(deck_id, folder_id)
            else:
                move_deck_to_folder(deck_id, folder_id)
        elif "move_folder_to_folder" in request.form:
            folder_id = request.form["folder_id"]
            new_parent_folder_id = request.form["new_parent_folders"]
            move_folder_to_folder(folder_id, new_parent_folder_id)
        elif "delete_folder" in request.form:
            folder_id = request.form["folder_id"]
            delete_folder(folder_id)
        elif "new_folder" in request.form:
            folder_title = request.form["new_folder_title"]
            new_folder(g.user["id"], g.folder, folder_title)
        elif "open_folder" in request.form:
            folder_id = request.form["folder_id"]
            open_folder(folder_id)
        elif "prev_folder" in request.form:
            open_prev_folder()
        elif "search" in request.form:
            search_term, search_function = handle_search(request.form)
    
    decks = get_all_user_decks(g.user["id"], g.folder["id"])
    decks = apply_filter(decks, "title", search_term, filter_function=search_function)

    routines = get_all_user_routines(g.user["id"])

    classes = get_all_user_controlled_classes(g.user["id"])

    child_folders = get_all_immediate_child_folders(g.folder["id"])

    all_folders = get_all_folders_orderered(get_user_root_folder(g.user["id"])["id"], [])

    folder_paths = []
    for folder in all_folders:
        folder_paths.append(get_formatted_folder_path(folder["id"], ""))
    
    return render_template("decks/all_user.html",
     decks=decks, user=g.user, routines=routines, classes=classes,
      parent_folder=g.folder, child_folders=child_folders,
       folder_paths=folder_paths, all_folders=all_folders)

@bp.route("/public_decks", methods=("GET", "POST"))
@login_required
def all_public():
    db = get_db()
    search_term = None
    search_function = None

    if request.method == "POST":
        if "search" in request.form:
            search_term, search_function = handle_search(request.form)
        if "study_deck" in request.form:
            deck_id = request.form["deck_id"]
            routine_id = request.form["routines"]
            return redirect(url_for("learn.begin_learn", deck_id=deck_id, routine_id=routine_id))
        if "save_deck" in request.form:
            deck_id = request.form["deck_id"]
            folder_id = request.form["folders"]
            save_deck_to_user(g.user["id"], deck_id, folder_id)
        if "unsave_deck" in request.form:
            deck_id = request.form["deck_id"]
            unsave_deck_from_user(g.user["id"], deck_id)
        if "save_deck_to_class" in request.form:
            deck_id = request.form["deck_id"]
            class_id = request.form["classes"]
            save_deck_to_class(class_id, deck_id)

    decks = db.execute(
        "SELECT * FROM deck WHERE is_public = ?",
        (str(to_bit(True)),)
    ).fetchall()
    decks = apply_filter(decks, "title", search_term, filter_function=search_function)
    decks_saved_info = get_saved_info(decks, "deck", g.user["id"])

    routines = get_all_user_routines(g.user["id"])

    classes = get_all_user_controlled_classes(g.user["id"])

    folders = get_all_folders_orderered(get_user_root_folder(g.user["id"])["id"], [])

    folder_paths = []
    for folder in folders:
        folder_paths.append(get_formatted_folder_path(folder["id"], ""))

    return render_template("decks/all_public.html",
     decks=decks, saved_info=decks_saved_info, routines=routines,
      folders=folders, folder_paths=folder_paths, classes=classes)

@bp.route("/create", methods=("GET", "POST"))
@login_required
def create():
    if request.method == "POST":
        deck_name = request.form["deck_name"]
        terms = request.form["terms"]
        intra_term_delimiter = request.form["intra_term_delimiter"]
        is_public = request.form["is_public"] == "1"

        error = None
        if deck_name is None:
            error = "Deck name is required"

        if error is None:
            db = get_db()
            cursor = db.cursor()
            try:

                cursor.execute(
                    "INSERT INTO deck (owner_id, folder_id, title, is_public) VALUES (?, ?, ?, ?)",
                    (str(g.user['id']), str(g.folder["id"]), deck_name, to_bit(is_public),)
                )
                db.commit()

                deck_id = cursor.lastrowid
                for line in terms.split("\n"):
                    question, answer = line.split(intra_term_delimiter)
                    db.execute(
                        "INSERT INTO term (deck_id, question, answer) VALUES (?, ?, ?)",
                        (str(deck_id), question, answer,)
                    )
                    db.commit()

                return redirect(url_for("decks.view_deck", deck_id=deck_id))
            except db.IntegrityError:
                error = "Deck name must be unique"

        flash(error) 
    
    return render_template("decks/create.html")

@bp.route("/view/<deck_id>")
@login_required
@member_deck_view
def view_deck(deck_id):
    db = get_db()
    deck = db.execute(
        "SELECT * FROM deck WHERE id = ?",
        (str(deck_id),)
    ).fetchone()

    terms = db.execute(
        "SELECT * FROM term WHERE deck_id = ?",
        (str(deck_id),)
    ).fetchall()

    return render_template("decks/deck.html", deck=deck, terms=terms)

@bp.route("/update/<deck_id>", methods=("GET", "POST"))
@login_required
@owner_deck_view
def update(deck_id):
    db = get_db()

    if request.method == "POST":
        deck_name = request.form["deck_name"]
        terms = request.form["terms"]
        intra_term_delimiter = request.form["intra_term_delimiter"]
        is_public = request.form["is_public"] == "1"

        error = None
        if deck_name is None:
            error = "Deck name is required"

        if error is None:
            db.execute(
                "UPDATE deck SET title = ?, is_public = ?, modified = CURRENT_TIMESTAMP WHERE id = ?",
                (deck_name, to_bit(is_public), str(deck_id),)
            )
            db.commit()

            db.execute(
                "DELETE FROM term WHERE deck_id = ?",
                (str(deck_id),)
            )
            db.commit()

            for line in terms.split("\n"):
                question, answer = line.split(intra_term_delimiter)
                db.execute(
                    "INSERT INTO term (deck_id, question, answer) VALUES (?, ?, ?)",
                    (str(deck_id), question, answer,)
                )
                db.commit()

            return redirect(url_for("decks.view_deck", deck_id=deck_id))

        flash(error) 

    current_deck = db.execute(
        "SELECT * FROM deck WHERE id = ?",
        (str(deck_id),)
    ).fetchone()

    terms = db.execute(
        "SELECT * FROM term WHERE deck_id = ?",
        (str(deck_id),)
    ).fetchall()

    return render_template("decks/update.html", deck=current_deck, terms=terms)

@bp.route("/delete/<deck_id>", methods=("GET", "POST"))
@login_required
@owner_deck_view
def delete(deck_id):
    db = get_db()
    if request.method == "POST":
        password = request.form["password"]
        
        error = None

        if password is None:
            error = "Password is required"

        if error is None:
            if check_password_hash(g.user["password"], password):
                db.execute(
                    "DELETE FROM deck WHERE id = ?",
                    (str(deck_id),)
                )
                db.commit()
                db.execute(
                    "DELETE FROM save_deck WHERE deck_id = ?",
                    (str(deck_id),)
                )
                db.commit()
                return redirect(url_for("decks.all_user"))
            else:
                error = "Incorrect password"
        
        flash(error)

    deck = db.execute(
        "SELECT * FROM deck WHERE id = ?",
        (str(deck_id),)
    ).fetchone()

    return render_template("decks/delete.html", deck=deck)
