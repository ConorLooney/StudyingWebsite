from flask import (
    request, redirect, url_for
)
from study.db import get_db

def get_question_answer(term_id):
    db = get_db()
    current_term = db.execute(
        "SELECT * FROM term WHERE id = ?",
        (str(term_id),)
    ).fetchone()
    return current_term["question"], current_term["answer"]

def split_into_words(answer):
    # Word is defined as characters between spaces, characters including grammer
    # e.g. "He was mad" -> ["He", "was", "mad"]
    # "He? He, he was mad!" -> ["He?", "He," "he", "was", "mad!""]
    return answer.split(" ")

def cover_words(words):
    # if few words, my cover 0 by chance
    # if not hitting this minimum then will add in some
    covered_words_minimum = 1
    # percentage of covered words of all words
    # e.g. 0.25 means one quarter of words are covered
    covered_words_proportion = 0.2
    # default map of all uncovered
    covered_words_map = [False] * len(words)
    
    covered_words_ideal_count = max(covered_words_minimum, covered_words_proportion * len(words))
    
    covered_count = covered_words_map.count(True)
    while covered_count < covered_words_ideal_count:
        covered_words_map[int(random.random() * len(covered_words_map))] = 1
        covered_count = covered_words_map.count(True)
    
    return covered_words_map

@bp.route("/<deck_id>/<routine_id>/<term_id>/<routine_position>/fill_in_blank", methods=("GET", "POST"))
@login_required
@member_deck_view
@member_routine_view
def fill_in_blanks(deck_id, routine_id, term_id, routine_position):
    if request.method == "POST":
        is_correct = True
        for correct_answer in request.form.keys():
            given_answer = request.form[correct_answer]
            is_correct = is_correct and given_answer == correct_answer
            if not is_correct:
                queue_to_correct(term_id, given_answer)
        db = get_db()
        db.execute(
            "INSERT INTO attempt (step, term_id, user_id, is_correct) VALUES (?, ?, ?, ?)",
            ("f", str(term_id), str(g.user["id"]), str(to_bit(is_correct)),)
        )
        db.commit()
        routine_position = int(routine_position) + 1
        return redirect(url_for("learn.learn", deck_id=deck_id, routine_id=routine_id,
            term_id=term_id, routine_position=routine_position))
            
    question, answer = get_question_answer(term_id)
    words = split_into_words(answer)
    covered_words_map = cover_words(words)
    return render_template("learn/fill_in_blanks.html", question=question,
    words=words, covered_words_map=covered_words_map)