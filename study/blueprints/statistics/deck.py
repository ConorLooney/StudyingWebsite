from flask import render_template, g, request
from study.auth import login_required
from study.db import get_db, to_bool
from study.utility.folder import get_folder_path
import time
import datetime
import json

from .main import bp

def gen_json_string_summary_accuracy(total_correct, total_incorrect):
    summary = {
        "cols":[
            {"id":'A', 'type':'string'},
            {"id":'B', 'type':'number'},
        ],
        "rows":[
            {"c":[
                {"v":"Total Correct"},
                {"v":total_correct},
            ]},
            {"c":[
                {"v":"Total Incorrect"},
                {"v":total_incorrect},
            ]},
        ],
    }
    return summary

def gen_json_string_summary_frequency(days, frequencies):
    day_values = [{"v":day} for day in days]
    frequency_values = [{"v":frequency} for frequency in frequencies]
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
        day = time.gmtime(attempt["unixepoch(created)"])
        # month is 0 indexed in google charts, indexed from 1 with time library so subtract 1
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

def get_max_date_range(terms):
    db = get_db()
    smallest_time = None
    biggest_time = None

    ask_attempts = []
    flashcard_attempts = []
    multiple_attempts = []
    correct_attempts = []
    for term in terms:
        ask_attempts.extend(db.execute(
            "SELECT id, term_id, user_id, unixepoch(created), is_correct, step \
            FROM attempt WHERE user_id = ? AND term_id = ? AND step = ?",
            (str(g.user["id"]), str(term["id"]), "a")
        ).fetchall())

        flashcard_attempts.extend(db.execute(
            "SELECT id, term_id, user_id, unixepoch(created), is_correct, step \
            FROM attempt WHERE user_id = ? AND term_id = ? AND step = ?",
            (str(g.user["id"]), str(term["id"]), "f",)
        ).fetchall())

        multiple_attempts.extend(db.execute(
            "SELECT id, term_id, user_id, unixepoch(created), is_correct, step \
            FROM attempt WHERE user_id = ? AND term_id = ? AND step = ?",
            (str(g.user["id"]), str(term["id"]), "m",)
        ).fetchall())

        correct_attempts.extend(db.execute(
            "SELECT id, term_id, user_id, unixepoch(created), is_correct, step \
            FROM attempt WHERE user_id = ? AND term_id = ? AND step = ?",
            (str(g.user["id"]), str(term["id"]), "c",)
        ).fetchall())

        for attempt in ask_attempts + flashcard_attempts + multiple_attempts + correct_attempts:
            created_time = int(attempt['unixepoch(created)'])
            if smallest_time is None or created_time < smallest_time:
                smallest_time = created_time
            if biggest_time is None or created_time > biggest_time:
                biggest_time = created_time
    
    return biggest_time, smallest_time

@bp.route("/deck/<deck_id>", methods=("GET", "POST"))
@login_required
def deck(deck_id):
    db = get_db()

    terms = db.execute(
        "SELECT * FROM term WHERE deck_id = ?",
        (str(deck_id),)
    ).fetchall()

    if len(terms) == 0:
        return render_template("statistics/empty.html")

    biggest_time, smallest_time = get_max_date_range(terms)
    start_from_epoch = smallest_time
    end_from_epoch = biggest_time

    if request.method == "POST":
        date_filter_start = request.form["filter_start"]
        date_filter_end = request.form["filter_end"]
        start_from_epoch = (datetime.datetime.fromisoformat(date_filter_start)).timestamp()
        end_from_epoch = (datetime.datetime.fromisoformat(date_filter_end)).timestamp()

    date_filter_start = datetime.date.fromtimestamp(start_from_epoch)
    date_filter_end = datetime.date.fromtimestamp(end_from_epoch)

    # increase end from epoch by day because datetime timestamp is seconds
    # from the very beginning of the day, so to include attempts made on that
    # day it is incremented by a day to cover the whole day
    end_from_epoch += 86400

    terms_ask_data = []
    terms_flashcard_data = []
    terms_correct_data = []
    terms_multiple_data = []

    for term in terms:
        ask_attempts = db.execute(
            "SELECT id, term_id, user_id, unixepoch(created), is_correct, step\
            FROM attempt WHERE user_id = ? AND term_id = ? AND step = ?\
            AND unixepoch(created) >= ? AND unixepoch(created) <= ?",
            (str(g.user["id"]), str(term["id"]), "a", start_from_epoch, end_from_epoch)
        ).fetchall()
        flashcard_attempts = db.execute(
            "SELECT id, term_id, user_id, unixepoch(created), is_correct, step\
            FROM attempt WHERE user_id = ? AND term_id = ? AND step = ?\
            AND unixepoch(created) >= ? AND unixepoch(created) <= ?",
            (str(g.user["id"]), str(term["id"]), "f", start_from_epoch, end_from_epoch)
        ).fetchall()
        correct_attempts = db.execute(
            "SELECT id, term_id, user_id, unixepoch(created), is_correct, step\
            FROM attempt WHERE user_id = ? AND term_id = ? AND step = ?\
            AND unixepoch(created) >= ? AND unixepoch(created) <= ?",
            (str(g.user["id"]), str(term["id"]), "c", start_from_epoch, end_from_epoch)
        ).fetchall()
        multiple_attempts = db.execute(
            "SELECT id, term_id, user_id, unixepoch(created), is_correct, step\
            FROM attempt WHERE user_id = ? AND term_id = ? AND step = ?\
            AND unixepoch(created) >= ? AND unixepoch(created) <= ?",
            (str(g.user["id"]), str(term["id"]), "m", start_from_epoch, end_from_epoch)
        ).fetchall()

        terms_ask_data.append(summarise_term_ask_attempts(ask_attempts))
        terms_flashcard_data.append(summarise_term_flashcard_attempts(flashcard_attempts))
        terms_correct_data.append(summarise_term_correct_attempts(correct_attempts))
        terms_multiple_data.append(summarise_term_multiple_attempts(multiple_attempts))
    
    json_terms = [json.dumps(dict(t)) for t in terms]

    deck = db.execute(
        "SELECT title, folder_id FROM deck WHERE id = ?",
        (str(deck_id),)
    ).fetchone()
    folder = deck["folder_id"]
    deck_path = get_folder_path(folder, "")
    deck_title = deck["title"]

    max_date = datetime.date.today().isoformat()
    min_date = max_date if smallest_time is None else datetime.datetime.fromtimestamp(smallest_time).date()

    return render_template("statistics/deck.html", terms=terms,
    start_date=date_filter_start, end_date=date_filter_end, min_date=min_date, max_date=max_date,
    deck_path=deck_path, deck_title=deck_title,
    json_terms=json_terms, terms_ask_data=terms_ask_data,
    terms_flashcard_data=terms_flashcard_data,
    terms_correct_data=terms_correct_data,
    terms_multiple_data=terms_multiple_data)
