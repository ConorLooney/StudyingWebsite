from flask import (
    render_template, g, request, redirect, url_for
)
from study.utility.general import (
    unsave_deck_from_user, get_all_user_routines, 
    get_all_user_decks, get_all_user_controlled_classes
)
from study.utility.folder import (
    get_all_immediate_child_folders, new_folder, open_folder, open_prev_folder,
    move_deck_to_folder, move_saved_deck_to_folder, delete_folder, get_formatted_folder_path,
    rename_folder, move_folder_to_folder, get_user_root_folder, get_all_folders_orderered
)
from study.db import get_db
from study.auth import login_required
from study.search_utility import handle_search, apply_filter
from .main import bp

@bp.route("/see_user", methods=("GET", "POST"))
@login_required
def see_user():
    search_term = None
    search_function = None
    
    if request.method == "POST":
        if "new_deck" in request.form:
            return redirect(url_for("decks.create"))
        elif "study_deck" in request.form:
            deck_id = request.form["deck_id"]
            routine_id = request.form["routines"]
            return redirect(url_for("learn.begin_learn", deck_id=deck_id, routine_id=routine_id))
        elif "unsave_deck" in request.form:
            deck_id = request.form["deck_id"]
            unsave_deck_from_user(g.user["id"], deck_id)
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