from flask import (
    flash, session, g
)
from study.db import get_db

def get_all_immediate_child_folders(folder_id):
    db = get_db()

    children = db.execute(
        "SELECT * FROM folder WHERE parent_id = ?",
        (str(folder_id),)
    ).fetchall()

    return children

def get_all_descendants(folder_id, children):
    latest = get_all_immediate_child_folders(folder_id)
    children.extend(latest)
    for folder in latest:
        get_all_descendants(folder["id"], children)
    return children

def move_folder_to_folder(moving_folder_id, new_parent_folder_id):
    db = get_db()

    if moving_folder_id == new_parent_folder_id:
        error = "Error: Cannot move folder into itself"
        flash(error)
        return

    # cannot move folder into any of its children
    # or any children of them and so on
    all_descendants = get_all_descendants(moving_folder_id, [])
    for folder in all_descendants:
        if int(folder["id"]) == int(new_parent_folder_id):
            error = "Error: Canont move folder into a descendant folder"
            flash(error)
            return
    
    db.execute(
        "UPDATE folder SET parent_id = ? WHERE id = ?",
        (str(new_parent_folder_id), str(moving_folder_id),)
    )
    db.commit()

def rename_folder(folder_id, new_title):
    db = get_db()
    db.execute(
        "UPDATE folder SET title = ? WHERE id = ?",
        (str(new_title), str(folder_id),)
    )
    db.commit()

"""Return string of form root\\first_title\\second_title\\...\\folder_title"""
def get_folder_path(folder_id, path):
    db = get_db()
    folder = db.execute(
        "SELECT * FROM folder WHERE id = ?",
        (str(folder_id),)
    ).fetchone()
    parent_folder = db.execute(
        "SELECT * FROM folder WHERE id = ?",
        (str(folder["parent_id"]),)
    ).fetchone()
    if parent_folder is None:
        return folder["title"]
    else:
        return get_folder_path(parent_folder["id"], path) + "/" + folder["title"]

def get_formatted_folder_path(folder_id, path):
    path = get_folder_path(folder_id, path)
    depth = path.count("/")
    folder = path.split("/")
    latest = folder[len(folder)-1]
    return depth * 2 * "⠀" + latest

"""Return a list of all folders in order of depth descending from parent id


For example: a structure with siblings A and B in folder root
A has two children, X and Y
B has two children, Z and W
Result should be: 
root, A, X, Y, B, Z, W"""
def get_all_folders_orderered(parent_id, result):
    db = get_db()

    parent = db.execute(
        "SELECT * FROM folder WHERE id = ?",
        (str(parent_id),)
    ).fetchone()
    result.append(parent)

    children = get_all_immediate_child_folders(parent_id)
    
    for child in children:
        get_all_folders_orderered(child["id"], result)
    return result

def delete_folder(folder_id):
    db = get_db()
    decks_in_folder = db.execute(
        "SELECT * FROM deck WHERE folder_id = ?",
        (str(folder_id),)
    ).fetchall()
    decks_saved_in_folder = db.execute(
        "SELECT * FROM save_deck WHERE folder_id = ?",
        (str(folder_id),)
    ).fetchall()
    folders_in_folder = db.execute(
        "SELECT * FROM folder WHERE parent_id = ?",
        (str(folder_id),)
    ).fetchall()

    if len(decks_in_folder) > 0 or len(decks_saved_in_folder) > 0 or len(folders_in_folder) > 0:
        error = "Error: Cannot delete folder with contents"
        flash(error)
        return
    
    db.execute(
        "DELETE FROM folder WHERE id = ?",
        (str(folder_id),)
    )
    db.commit()

def move_deck_to_folder(deck_id, folder_id):
    db = get_db()
    db.execute(
        "UPDATE deck SET folder_id = ? WHERE id = ?",
        (str(folder_id), str(deck_id),)
    )
    db.commit()

def move_saved_deck_to_folder(user_id, deck_id, folder_id):
    db = get_db()
    db.execute(
        "UPDATE save_deck SET folder_id = ? WHERE user_id = ? AND deck_id = ?",
        (str(folder_id), str(user_id), str(deck_id),)
    )
    db.commit()

def open_folder(folder_id):
    db = get_db()
    folder = db.execute(
        "SELECT * FROM folder WHERE id = ?",
        (str(folder_id),)
    ).fetchone()
    session["folder_id"] = folder_id
    g.folder = folder

def open_prev_folder():
    folder = g.folder
    parent_id = folder["parent_id"]
    if parent_id == -1:
        error = "Error: No folders above root"
        flash(error)
        return
    open_folder(parent_id)

def new_folder(user_id, parent_folder, folder_title):
    db = get_db()
    db.execute(
        "INSERT INTO folder (title, owner_id, parent_id) VALUES (?, ?, ?)",
        (str(folder_title), str(user_id), str(parent_folder["id"]),)
    )
    db.commit()

"""Each user has their own root folder

A root folder has a parent id as a rogue value of -1"""
def get_user_root_folder(user_id):
    db = get_db()
    folder = db.execute(
        "SELECT * FROM folder WHERE parent_id = ? AND owner_id = ?",
        (str(-1), str(user_id),)
    ).fetchone()
    return folder