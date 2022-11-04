from flask import request, render_template
from study.auth import login_required, member_routine_view, member_deck_view
import random

from .main import bp
from .utility import get_term, add_to_queue_to_correct, record_attempt, redirect_to_next

def read_form(words):
    answers = {}
    for word_index in request.form.keys():
        given_answer = request.form[word_index].replace("\r", "").replace("\n", "")
        word_index = int(word_index)
        correct_answer = words[word_index].replace("\r", "").replace("\n", "")
        answers[correct_answer] = given_answer
        
    whole_answer = ""
    for i in range(len(words)):
        if str(i) in request.form.keys():
            whole_answer += request.form[str(i)].replace("\r", "").replace("\n", "")
        else:
            whole_answer += words[i]
        whole_answer += " "

    return answers, whole_answer

def split_into_words(answer):
    # Word is defined as characters between spaces, characters including grammer
    # e.g. "He was mad" -> ["He", "was", "mad"]
    # "He? He, he was mad!" -> ["He?", "He," "he", "was", "mad!""]
    return answer.split(" ")

def blank_words(words, blank_minimum=1, blank_proportion=0.2):
    blank_map = [False] * len(words)
    ideal_blank_count = max(blank_minimum, int(blank_proportion * len(words)))
    blank_count = 0
    while blank_count < ideal_blank_count:
        to_blank_index = int(random.random() * len(words))
        # already blank
        if blank_map[to_blank_index]:
            continue
        else:
            words[to_blank_index] = "__" + str(blank_count + 1) + "__"
            blank_map[to_blank_index] = True
            blank_count += 1
    return words, blank_map

@bp.route("/<deck_id>/<routine_id>/<term_id>/<routine_position>/fill_in_blank", methods=("GET", "POST"))
@login_required
@member_deck_view
@member_routine_view
def fill_in_blanks(deck_id, routine_id, term_id, routine_position):
    # get the question
    # get the answer
    # fill in random words with __n__ where n is the amount of blank words to that one
    # e.g. ich habe -> ich __1__ 
    # e.g.  In Of Mice and Men John Steinbeck presents Slim as someone to be admired -> In Of Mice and Men John __1__ presents __2__ as someone to be __3__
    # pass this to template to display each word
    # then an input is made for each blank (using blank map to find the blanks)
    # when the answers are given we get the index of the word each input is trying to be
    # we know the answer and so get the correct answer from this index
    term = get_term(term_id)
    question = term["question"]
    answer = term["answer"]
    words = split_into_words(answer)

    if request.method == "POST":
        all_correct = True
        
        answers, whole_answer = read_form(words)
        for correct_answer, given_answer in answers.items():
            is_correct = given_answer == correct_answer
            if not is_correct:
                all_correct = False
                add_to_queue_to_correct(term_id, whole_answer)
        
        record_attempt("b",term_id, all_correct)
        return redirect_to_next(deck_id, routine_id, term_id, routine_position)

    blanked_words, blanked_map = blank_words(words)


    return render_template("learn/fill_in_blanks.html", question=question,
    blanked_words=blanked_words, blanked_map=blanked_map)