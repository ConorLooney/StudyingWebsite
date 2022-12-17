from enum import Enum

class Step:

    def __init__(self, name, abbreviation, run_once_per_session=False):
        self.name = name
        self.abbreviation = abbreviation
        self.run_once_per_session = run_once_per_session

class Steps(Enum):
    ASK = Step("ask", "a")
    CORRECT = Step("correct", "c")
    FLASHCARD = Step("flashcard", "f")
    MULTIPLE_CHOICE = Step("multiple choice", "m")
    FILL_IN_BLANKS = Step("fill in blanks", "b")