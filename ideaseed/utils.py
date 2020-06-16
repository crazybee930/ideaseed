from typing import Optional
from typing import *
import colr
import inquirer
from os import path

def dye(
    text: str,
    fg: Optional[int] = None,
    bg: Optional[int] = None,
    style: Optional[str] = None,
    no_closing: bool = False,
):
    return colr.color(
        text=text,
        fore=f"{fg:x}" if fg is not None else None,
        back=f"{bg:x}" if bg is not None else None,
        style=style,
        no_closing=no_closing,
    )


def ask(*questions) -> List[Any]:
    if len(questions) == 1:
        # No need to turn the hash into a tuple, just return the only value
        questions[0].name = "ans"
        return inquirer.prompt(questions)["ans"]

    for i, _ in enumerate(questions):
        questions[i].name = i
    # Ask dem questions
    answers = inquirer.prompt(questions)
    # Turn into a list of tuple
    answers = list(answers.items())
    # Sort by key
    answers = sorted(answers, key=lambda a: a[0])
    # Get only the answers
    answers = [a[1] for a in answers]
    return answers

def get_token_cache_filepath() -> str:
    return path.join(path.dirname(path.dirname(__file__)), f'.auth-cache')
