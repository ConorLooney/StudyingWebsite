from flask import g
import json
import time

from study.db import get_db

class ChartData:

    def __init__(self, cols):
        """Cols is of [[id, type], [id, type], [...], ...]"""
        self.data = {
            "cols":[
                
            ],
            "rows":[

            ]
        }
        for col in cols:
            self.data["cols"].append({"id":col[0], "type":col[1]})

    def newRow(self, *args):
        """Each arg row, as in a list of values"""
        for i in range(len(args)):
            values = []
            for value in args[i]:
                values.append({"v":value})
            self.data["rows"].append(
                {"c":values}
            )

def get_accuracy_template():
    return {
        "cols":[
            {"id":'A', 'type':'string'},
            {"id":'B', 'type':'number'},
        ],
        "rows":[
            {"c":[
                {"v":"Total Correct"},
            ]},
            {"c":[
                {"v":"Total Incorrect"},
            ]},
        ],
    }

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