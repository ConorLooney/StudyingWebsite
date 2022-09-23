from flask import (
    Blueprint, render_template, g
)
from study.auth import login_required
from study.db import get_db, to_bool
import time
import json

bp = Blueprint("statistics", __name__, url_prefix="/statistics")

def gen_json_string_summary_accuracy(total_correct, total_incorrect):
    summary = {
        "cols":[
            {"id":'A', 'type':'string'},
            {"id":'B', 'type':'number'},
        ],
        "rows":[
            {"c":[
                {"v":"total correct"},
                {"v":total_correct},
            ]},
            {"c":[
                {"v":"total incorrect"},
                {"v":total_incorrect},
            ]},
        ],
    }
    return summary

def gen_json_string_summary_frequency(days, frequencies):
    day_values = [{"v":day} for day in days]
    print(days)
    frequency_values = [{"v":frequency for frequency in frequencies}]
    cells = []
    for i in range(len(day_values)):
        cell = {
            "c":[day_values[i], frequency_values[i]]
            }
        cells.append(cell)
    summary = {
        "cols":[
            {"id":'A', 'type':'date'},
            {"id":'B', 'type':'number'},
        ],
        "rows":cells,
    }
    return summary

def summarise_deck_flashcard_attempts(attempts):
    if len(attempts) == 0:
        return {}
    days = []
    frequencies = []
    for attempt in attempts:
        day = time.gmtime(attempt["unixepoch(created)"])
        day = "Date(" + str(day.tm_year) + ", " + str(day.tm_mon) + ", " + str(day.tm_mday) + ")"
        if day in days:
            index = days.index(day)
            frequencies[index] += 1
        else:
            days.append(day)
            frequencies.append(1)
    summary = gen_json_string_summary_frequency(days, frequencies)
    return json.dumps(summary)

def summarise_deck_multiple_attempts(attempts):
    return summarise_deck_ask_attempts(attempts)

def summarise_deck_correct_attempts(attempts):
    return summarise_deck_ask_attempts(attempts)

def summarise_deck_ask_attempts(attempts):
    if len(attempts) == 0:
        return {}
    total_correct = 0
    total_incorrect = 0
    for attempt in attempts:
        is_correct = to_bool(attempt["is_correct"])
        if is_correct:
            total_correct += 1
        else:
            total_incorrect += 1
    summary = gen_json_string_summary_accuracy(total_correct, total_incorrect)
    return json.dumps(summary)

def summarise_term_flashcard_attempts(attempts):
    if len(attempts) == 0:
        return {}
    days = []
    frequencies = []
    for attempt in attempts:
        print(dict(attempt))
        day = time.gmtime(attempt["unixepoch(created)"])
        day = "Date(" + str(day.tm_year) + ", " + str(day.tm_mon-1) + ", " + str(day.tm_mday) + ")"
        if day in days:
            index = days.index(day)
            frequencies[index] += 1
        else:
            days.append(day)
            frequencies.append(1)
    summary = gen_json_string_summary_frequency(days, frequencies)
    return json.dumps(summary)

def summarise_term_multiple_attempts(attempts):
    return summarise_term_ask_attempts(attempts)

def summarise_term_correct_attempts(attempts):
    return summarise_term_ask_attempts(attempts)

def summarise_term_ask_attempts(attempts):
    if len(attempts) == 0:
        return {}
    total_correct = 0
    total_incorrect = 0
    for attempt in attempts:
        is_correct = to_bool(attempt["is_correct"])
        if is_correct:
            total_correct += 1
        else:
            total_incorrect += 1
    summary = gen_json_string_summary_accuracy(total_correct, total_incorrect)
    return json.dumps(summary)

@bp.route("/all")
@login_required
def all():
    db = get_db()

    decks = db.execute(
        "SELECT DISTINCT deck.id, deck.title FROM deck \
        JOIN term ON term.deck_id = deck.id \
        JOIN attempt ON attempt.term_id = term.id \
        WHERE attempt.user_id = ?",
        (str(g.user["id"]),)
    ).fetchall()

    print()
    print("DECKS:")
    print([dict(d) for d in decks])
    print()
    print("attempts:")
    attempts = db.execute(
        "SELECT * FROM attempt WHERE user_id = ?",
        (str(g.user["id"]),)
    ).fetchall()
    print([dict(a) for a in attempts])
    print(":")
    attempts = db.execute(
        "SELECT * FROM term \
        JOIN attempt ON attempt.term_id = term.id \
        WHERE attempt.user_id = ?",
        (str(g.user["id"]),)
    ).fetchall()
    print([dict(a) for a in attempts])
    print()
    
    decks_ask_data = []
    decks_flashcard_data = []
    decks_correct_data = []
    decks_multiple_data = []

    for deck in decks:
        terms = db.execute(
            "SELECT * FROM term WHERE deck_id = ?",
            (str(deck["id"]),)
        ).fetchall()
        ask_attempts = []
        flashcard_attempts = []
        multiple_attempts = []
        correct_attempts = []
        for term in terms:
            ask_attempts.extend(db.execute(
                "SELECT id, term_id, user_id, unixepoch(created), is_correct, step FROM attempt WHERE user_id = ? AND term_id = ? AND step = ?",
                (str(g.user["id"]), str(term["id"]), "a")
            ).fetchall())
            flashcard_attempts.extend(db.execute(
                "SELECT id, term_id, user_id, unixepoch(created), is_correct, step FROM attempt WHERE user_id = ? AND term_id = ? AND step = ?",
                (str(g.user["id"]), str(term["id"]), "f")
            ).fetchall())
            multiple_attempts.extend(db.execute(
                "SELECT id, term_id, user_id, unixepoch(created), is_correct, step FROM attempt WHERE user_id = ? AND term_id = ? AND step = ?",
                (str(g.user["id"]), str(term["id"]), "m")
            ).fetchall())
            correct_attempts.extend(db.execute(
                "SELECT id, term_id, user_id, unixepoch(created), is_correct, step FROM attempt WHERE user_id = ? AND term_id = ? AND step = ?",
                (str(g.user["id"]), str(term["id"]), "c")
            ).fetchall())
        
        decks_ask_data.append(summarise_deck_ask_attempts(ask_attempts))
        decks_flashcard_data.append(summarise_deck_flashcard_attempts(flashcard_attempts))
        decks_multiple_data.append(summarise_deck_multiple_attempts(multiple_attempts))
        decks_correct_data.append(summarise_deck_correct_attempts(correct_attempts))

    print("dict deck")
    for deck in decks:
        print(json.dumps(dict(deck)))
    json_decks = [json.dumps(dict(deck)) for deck in decks]

    print(decks_ask_data)
    print("flashcard:")
    print(decks_flashcard_data)
    return render_template("statistics/all.html", decks=decks, json_decks=json_decks,
    decks_ask_data=decks_ask_data, decks_flashcard_data=decks_flashcard_data,
    decks_correct_data=decks_correct_data, decks_multiple_data=decks_multiple_data)

@bp.route("/deck/<deck_id>")
@login_required
def deck(deck_id):
    db = get_db()

    terms = db.execute(
        "SELECT * FROM term WHERE deck_id = ?",
        (str(deck_id),)
    ).fetchall()

    terms_ask_data = []
    terms_flashcard_data = []
    terms_correct_data = []
    terms_multiple_data = []

    for term in terms:
        ask_attempts = db.execute(
            "SELECT id, term_id, user_id, unixepoch(created), is_correct, step FROM attempt WHERE user_id = ? AND term_id = ? AND step = ?",
            (str(g.user["id"]), str(term["id"]), "a")
        ).fetchall()
        flashcard_attempts = db.execute(
            "SELECT id, term_id, user_id, unixepoch(created), is_correct, step FROM attempt WHERE user_id = ? AND term_id = ? AND step = ?",
            (str(g.user["id"]), str(term["id"]), "f")
        ).fetchall()
        correct_attempts = db.execute(
            "SELECT id, term_id, user_id, unixepoch(created), is_correct, step FROM attempt WHERE user_id = ? AND term_id = ? AND step = ?",
            (str(g.user["id"]), str(term["id"]), "c")
        ).fetchall()
        multiple_attempts = db.execute(
            "SELECT id, term_id, user_id, unixepoch(created), is_correct, step FROM attempt WHERE user_id = ? AND term_id = ? AND step = ?",
            (str(g.user["id"]), str(term["id"]), "m")
        ).fetchall()

        terms_ask_data.append(summarise_term_ask_attempts(ask_attempts))
        terms_flashcard_data.append(summarise_term_flashcard_attempts(flashcard_attempts))
        terms_correct_data.append(summarise_term_correct_attempts(correct_attempts))
        terms_multiple_data.append(summarise_term_multiple_attempts(multiple_attempts))
    
    json_terms = [json.dumps(dict(t)) for t in terms]

    return render_template("statistics/deck.html", terms=terms,
    json_terms=json_terms, terms_ask_data=terms_ask_data,
    terms_flashcard_data=terms_flashcard_data,
    terms_correct_data=terms_correct_data,
    terms_multiple_data=terms_multiple_data)
