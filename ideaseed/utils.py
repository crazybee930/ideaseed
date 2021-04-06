from __future__ import annotations

from random import randint
from typing import Any, Iterable, Union

import inquirer
from rich import print


def readable_on(background: str, light: str = "FFFFFF", dark: str = "000000") -> str:
    """
    Choses either ``light`` or ``dark`` based on the background color
    the text is supposed to be written on ``background`` (also given as an hex int)
    
    WARN: All the color strings must be exactly 6 digits long.
    
    >>> readable_text_color_on('FEFAFE')
    '000000'
    >>> readable_text_color_on('333333')
    'FFFFFF'
    """
    r, g, b = hex_to_rgb(background)
    luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255
    if luminance > 0.5:
        return dark
    else:
        return light


def hex_to_rgb(hexstring: Union[str, int]) -> tuple[int, int, int]:
    """
    Converts a hexstring (without initial '#') ``hexstring`` into a 
    3-tuple of ints in [0, 255] representing an RGB color
    
    >>> hex_to_rgb('FF00AA')
    (255, 0, 170)
    """
    if type(hexstring) is int:
        hexstring = f"{hexstring:6x}"
    return tuple(int(hexstring[i : i + 2], 16) for i in (0, 2, 4))


def get_random_color_hexstring() -> str:
    return f"{randint(0x0, 0xFFFFFF):6x}".upper()


def ask(*questions) -> Union[list[Any], Any]:
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


def ask_text(question: str):
    return ask(inquirer.Text("ans", message=question))


def answered_yes_to(question: str) -> bool:
    return ask(inquirer.Confirm("ans", message=question))


def english_join(items: list[str]) -> str:
    """
    Joins items in a sentence-compatible way, adding "and" at the end

    >>> english_join(["a", "b", "c"])
    'a, b and c'
    >>> english_join(["a"])
    'a'
    >>> english_join(["a", "b"])
    'a and b'
    """
    if not items:
        return ""
    if len(items) == 1:
        return items[0]
    return ", ".join(items[:-1]) + " and " + items[-1]


def print_dry_run(text: str):
    """
    Apply special formatting for dry-run specific messages
    """
    print(f"[black on yellow] DRY RUN [/]   [dim]{text}")


def error_message_no_object_found(objtype: str, objname: str) -> str:
    return (
        print(f"[red]Error: missing {objtype} {objname!r}")
        + """
TIP: Use --create-missing and ideaseed will ask you if you want to create missing labels, issues, projects, columns, milestones..."""
    )


def case_insensitive_find(haystack: Iterable[str], needle: str) -> str:
    for item in haystack:
        if item.lower() == needle.lower():
            return item

    return None


def remove_duplicates_in_list_of_dict(o: dict[Any, Union[Any, list]]) -> dict:
    """
    Remove duplicates in values of `o` of type `list`.
    """
    return {
        k: (list(dict.fromkeys(v)) if isinstance(v, list) else v) for k, v in o.items()
    }


if __name__ == "__main__":
    import doctest

    doctest.testmod()
