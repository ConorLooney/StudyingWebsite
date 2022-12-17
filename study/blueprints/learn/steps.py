class Step:

    def __init__(self, name, abbreviation, view_function_name, run_once_per_session=False):
        self.name = name
        self.abbreviation = abbreviation
        self.run_once_per_session = run_once_per_session
        self.view_function_name = view_function_name

ASK = Step("ask", "a", "learn.ask")
CORRECT = Step("correct", "c", "learn.correct")
FLASHCARD = Step("flashcard", "f", "learn.flashcard")
MULTIPLE_CHOICE = Step("multiple choice", "m", "learn.choice")
FILL_IN_BLANKS = Step("fill in blanks", "b", "learn.fill_in_blanks")
steps = [ASK, CORRECT, FLASHCARD, MULTIPLE_CHOICE, FILL_IN_BLANKS]

def get_step_from_abbreviation(abbreviation):
    for step in steps:
        if step.abbreviation == abbreviation:
            return step

def get_step_view_func_from_abbreviation(abbreviation):
    step = get_step_from_abbreviation(abbreviation)
    return step.view_function_name

def does_step_run_once_per_session(abbreviation):
    step = get_step_from_abbreviation(abbreviation)
    return step.run_once_per_session