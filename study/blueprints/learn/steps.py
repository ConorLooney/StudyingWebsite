class Step:

    def __init__(self, name, abbreviation, run_once_per_session=False):
        self.name = name
        self.abbreviation = abbreviation
        self.run_once_per_session = run_once_per_session

ASK = Step("ask", "a")
CORRECT = Step("correct", "c")
FLASHCARD = Step("flashcard", "f")
MULTIPLE_CHOICE = Step("multiple choice", "m")
FILL_IN_BLANKS = Step("fill in blanks", "b")
steps = [ASK, CORRECT, FLASHCARD, MULTIPLE_CHOICE, FILL_IN_BLANKS]

def get_step_from_abbreviation(abbreviation):
    for step in steps:
        if step.abbreviation == abbreviation:
            return step

def does_step_run_once_per_session(abbreviation):
    step = get_step_from_abbreviation(abbreviation)
    return step.run_once_per_session