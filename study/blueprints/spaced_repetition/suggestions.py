from flask import render_template, g, redirect, url_for
import datetime

from study.db import get_db
from .utility import calculateMemoryRetention, getDaysOfRevision
from .main import bp

class Suggestion:

    def __init__(self, spaced_repetition_setting, date, projectedMemoryRetention):
        self.spaced_repetition_setting = spaced_repetition_setting
        self.date = date
        self.projectedMemoryRetention = projectedMemoryRetention

def get_spaced_repetition_settings():
    """Return all spaced repetition settings by the logged in user"""
    db = get_db()
    spaced_repetition_settings = db.execute(
        "SELECT * FROM spaced_repetition_setting WHERE user_id = ?",
        (str(g.user["id"]),)
    ).fetchall()
    return spaced_repetition_settings

def get_study_sessions_ordered_by_date(deck_id, routine_id):
    """Return all study sessions by the logged in user of the given deck and routine
    ordered by date studied in descending order"""
    db = get_db()
    study_sessions = db.execute(
        "SELECT * FROM study_session WHERE deck_id = ? AND routine_id= ? AND user_id = ? ORDER BY date_studied DESC",
        (str(deck_id), str(routine_id), str(g.user["id"]),)
    ).fetchall()
    return study_sessions

def get_time_since_studying(date, deck_id, routine_id):
    """Return the time since the given deck and routine were studied together
    as a timedelta object. If the deck and routine have never been studied, return 0 and
    if the deck and routine have been studied after the given date return -1"""
    sessions = get_study_sessions_ordered_by_date(deck_id, routine_id)
    if len(sessions) == 0:
        return datetime.date.today() - datetime.date.today()
    else:
        most_recent_session = sessions[0]
        most_recent_study_date = most_recent_session["date_studied"]
        last_date_studied = datetime.date.fromisoformat(most_recent_study_date.split(" ")[0])
        # checking dates in the past is supported, so if the date is before the most
        # recent study date this means the time since studying is -1, rogue value
        if date < last_date_studied:
            return -1
        else:
            time_since_studying = date - last_date_studied
            return time_since_studying

def get_amount_of_times_studied(deck_id, routine_id):
    """Return number of times the given deck and routine have been studied
    together by the logged in user"""
    study_sessions = get_study_sessions_ordered_by_date(deck_id, routine_id)
    return len(study_sessions)

def get_suggestions(view_date, from_date=datetime.date.today()):
    """Return the settings that should be revised on the view date assuming
    optimal revision from the from date. From date is assumed to be today"""
    spaced_repetition_settings = get_spaced_repetition_settings()
    suggestions = []
    for setting in spaced_repetition_settings:
        deck_id = setting["deck_id"]
        routine_id = setting["routine_id"]
        threshold = setting["reminder_threshold"]
        steepness = setting["steepness_constant"]
        change = setting["change_constant"]

        time_since_studying = get_time_since_studying(from_date, deck_id, routine_id)
        times_studied = get_amount_of_times_studied(deck_id, routine_id)

        # list of days from the from date that should be revised on
        # e.g. [2, 5] means 2 days after from date and 5 days after from date, revise
        days = getDaysOfRevision(time_since_studying.days, times_studied,
        threshold, steepness, change)

        # view date must be after or equal to from date
        difference = view_date - from_date
        print(days)
        for day in days:
            if difference.days == day[0]:
                print("record suggestion")
                print(day)
                print(view_date)
                suggestions.append(Suggestion(setting, view_date, day[1]))
                break
    return suggestions

def get_deck(deck_id):
    db = get_db()
    return db.execute(
        "SELECT * FROM deck WHERE id = ?",
        (str(deck_id),)
    ).fetchone()

def get_decks(suggestions):
    """Return a dict of deck ids to decks for each deck id in the settings given"""
    decks = {}
    for suggestion in suggestions:
        setting = suggestion.spaced_repetition_setting
        decks[setting["deck_id"]] = get_deck(setting["deck_id"])
    return decks

def get_routine(routine_id):
    db = get_db()
    return db.execute(
        "SELECT * FROM routine WHERE id = ?",
        (str(routine_id),)
    ).fetchone()

def get_routines(suggestions):
    """Return a dict of routine ids to routines for each routine id in the settings given"""
    routines = {}
    for suggestion in suggestions:
        setting = suggestion.spaced_repetition_setting
        routines[setting["routine_id"]] = get_routine(setting["routine_id"])
    return routines

@bp.route("/suggestions/<day>/<month>/<year>")
def view_suggestions(day, month, year):
    date = datetime.date(int(year), int(month), int(day))

    # time_range number of days on either side of given date to be display
    time_range = 30
    day_suggestions = {}
    for i in range(time_range):
        day = date + datetime.timedelta(days=i)
        day_suggestions[day] = get_suggestions(day)

    decks = {}
    routines = {}
    for day in day_suggestions.keys():
        decks = decks | get_decks(day_suggestions[day])
        routines = routines | get_routines(day_suggestions[day])

    return render_template("spaced_repetition/suggestions.html",
    day_suggestions=day_suggestions, decks=decks, routines=routines)

@bp.route("/suggestions_today")
def suggestions_today():
    today = datetime.date.today()
    return redirect(url_for("spaced_repetition.view_suggestions",
     day=today.day, month=today.month, year=today.year))