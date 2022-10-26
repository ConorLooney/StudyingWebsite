from flask import (
    render_template, g, request, redirect, url_for
)
from study.utility.general import (
    save_deck_to_class, unsave_deck_from_user, save_deck_to_user, get_all_user_routines,
    get_saved_info, get_all_user_controlled_classes
)
from study.utility.folder import (
    get_user_root_folder, get_all_folders_orderered, get_formatted_folder_path
)
from study.db import get_db, to_bit
from study.auth import login_required
from study.search_utility import handle_search, apply_filter

from .main import bp

@bp.route("/see_public", methods=("GET", "POST"))
@login_required
def see_public():
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