from flask import (
    Blueprint, render_template, g, request, flash, redirect, url_for
)
from werkzeug.security import check_password_hash
from study.auth import private_deck_view, protected_deck_view
from study.db import get_db, to_bit
from study.auth import login_required, private_deck_view, protected_deck_view

bp = Blueprint("decks", __name__)

@bp.route("/", methods=("GET", "POST"))
@login_required
def all_user():
    search_term = None
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
            db = get_db()
            db.execute(
                "DELETE FROM save_deck WHERE deck_id = ? AND user_id = ?",
                (str(deck_id), str(g.user["id"]),)
            )
            db.commit()
        elif "search" in request.form:
            search_term = request.form["search_field"]
            search_criteria = request.form["search_criteria"]
            if search_term == "":
                search_term = None
                search_criteria = None
            if search_criteria == "equals":
                search_term = str(search_term)
            elif search_criteria == "contains":
                search_term = "%" + str(search_term) + "%"

    db = get_db()
    
    if search_term is None:
        decks = db.execute(
            "SELECT * FROM deck WHERE owner_id = ?",
            (str(g.user['id']))
        ).fetchall()
        decks.extend(db.execute(
            "SELECT * FROM deck \
            JOIN save_deck ON deck.id = save_deck.deck_id \
            WHERE save_deck.user_id = ?",
            (str(g.user["id"]),)
        ).fetchall())
    else:
        decks = db.execute(
            "SELECT * FROM deck WHERE owner_id = ? AND title LIKE ?",
            (str(g.user['id']), search_term,)
        ).fetchall()
        decks.extend(db.execute(
            "SELECT * FROM deck \
            JOIN save_deck ON deck.id = save_deck.deck_id \
            WHERE save_deck.user_id = ? AND title LIKE ?",
            (str(g.user["id"]), search_term,)
        ).fetchall())

    owned_info = []
    for deck in decks:
        if str(deck["owner_id"]) == str(g.user["id"]):
            owned_info.append(True) # cannot be saved
        else:
            owned_info.append(False)

    routines = db.execute(
        "SELECT * FROM routine WHERE owner_id = ?",
        (str(g.user['id']))
    ).fetchall()

    routines.extend(db.execute(
        "SELECT * FROM routine\
        JOIN save_routine ON save_routine.routine_id = routine.id\
        WHERE save_routine.user_id = ?",
        (str(g.user["id"]),)
    ).fetchall())

    return render_template("decks/all_user.html", decks=decks, owned_info=owned_info, routines=routines)

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
            try:

                db.execute(
                    "INSERT INTO deck (owner_id, title, is_public) VALUES (?, ?, ?)",
                    (str(g.user['id']), deck_name, to_bit(is_public),)
                )
                db.commit()

                deck_id = db.execute(
                    "SELECT * FROM deck WHERE title = ?",
                    (deck_name,)
                ).fetchone()['id']

                for line in terms.split("\n"):
                    print(line)
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
@protected_deck_view
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
@private_deck_view
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
            try:

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
            except db.IntegrityError:
                error = "Deck name must be unique"

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
@private_deck_view
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

@bp.route("/public_decks", methods=("GET", "POST"))
@login_required
def all_public():
    search_term = None

    if request.method == "POST":
        if "search" in request.form:
            search_term = request.form["search_field"]
            search_criteria = request.form["search_criteria"]
            if search_term == "":
                search_term = None
                search_criteria = None
            if search_criteria == "equals":
                search_term = str(search_term)
            elif search_criteria == "contains":
                search_term = "%" + str(search_term) + "%"
        if "study_deck" in request.form:
            deck_id = request.form["deck_id"]
            routine_id = request.form["routines"]
            return redirect(url_for("learn.begin_learn", deck_id=deck_id, routine_id=routine_id))
        if "save_deck" in request.form:
            deck_id = request.form["deck_id"]
            db = get_db()
            db.execute(
                "INSERT INTO save_deck (user_id, deck_id) VALUES (?, ?)",
                (str(g.user['id']), str(deck_id),)
            )
            db.commit()
        if "unsave_deck" in request.form:
            deck_id = request.form["deck_id"]
            db = get_db()
            db.execute(
                "DELETE FROM save_deck WHERE deck_id = ? AND user_id = ?",
                (str(deck_id), str(g.user["id"]),)
            )
            db.commit()

    db = get_db()

    if search_term is None:
        decks = db.execute(
            "SELECT * FROM deck WHERE is_public = ?",
            (str(to_bit(True)),)
        ).fetchall()
    else:
        decks = db.execute(
            "SELECT * FROM deck WHERE is_public = ? AND title LIKE ? ",
            (str(to_bit(True)), search_term,)
        ).fetchall()

    saved_info = []
    for deck in decks:
        if str(deck["owner_id"]) == str(g.user["id"]):
            saved_info.append(-1) # cannot be saved
            continue

        save_deck = db.execute(
            "SELECT * FROM save_deck WHERE deck_id = ? AND user_id = ?",
            (str(deck["id"]), str(g.user["id"]),)
        ).fetchall()

        if len(save_deck) > 0:
            saved_info.append(1) # already saved, should be unsaved
        else:
            saved_info.append(0) # can be saved

    routines = db.execute(
        "SELECT * FROM routine WHERE owner_id = ?",
        (str(g.user['id']))
    ).fetchall()

    return render_template("decks/all_public.html", decks=decks, saved_info=saved_info, routines=routines)