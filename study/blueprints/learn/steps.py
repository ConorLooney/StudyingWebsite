class Step:

    def __init__(self, name, abbreviation, view_function_name, run_once_per_session=False):
        self.name = name
        self.abbreviation = abbreviation
        self.run_once_per_session = run_once_per_session
        self.view_function_name = view_function_name

ASK = Step("Ask", "a", "learn.ask")
CORRECT = Step("Correct", "c", "learn.correct")
FLASHCARD = Step("Flashcard", "f", "learn.flashcard")
MULTIPLE_CHOICE = Step("Multiple Choice", "m", "learn.choice")
FILL_IN_BLANKS = Step("Fill in Blanks", "b", "learn.fill_in_blanks")
SORT = Step("Sort", "s", "learn.sort", run_once_per_session=True)
ORDER = Step("Order", "o", "learn.order", run_once_per_session=True)
steps = [ASK, CORRECT, FLASHCARD, MULTIPLE_CHOICE, FILL_IN_BLANKS, SORT, ORDER]

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

def get_all_steps():
    return steps