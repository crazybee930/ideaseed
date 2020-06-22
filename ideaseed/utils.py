from typing import Optional
from typing import *
import colr
import inquirer
from os import path
from random import randint


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


def readable_text_color_on(
    background: int, light: int = 0xFFFFFF, dark: int = 0x000000
) -> int:
    """
    Choses either ``light`` or ``dark`` based on the background color
    the text is supposed to be written on ``background`` (also given as an hex int)
    
    WARN: All the color ints must be exactly 6 digits long.
    
    >>> readable_text_color_on(0xFEFAFE)
    0
    >>> readable_text_color_on(0x333333)
    16777215
    """
    r, g, b = hex_to_rgb(f"{background:6x}")
    luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255
    if luminance > 0.5:
        return dark
    else:
        return light


def hex_to_rgb(hexstring: str) -> Tuple[int, int, int]:
    """
    Converts a hexstring (without initial '#') ``hexstring`` into a 
    3-tuple of ints in [0, 255] representing an RGB color
    
    >>> hex_to_rgb('FF00AA')
    (255, 0, 170)
    """
    return tuple(int(hexstring[i : i + 2], 16) for i in (0, 2, 4))  # skip '#'


def get_random_color_hexstring() -> str:
    return f"{randint(0x0, 0xFFFFFF):6x}".upper()


def ask(*questions) -> Union[List[Any], Any]:
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


def get_token_cache_filepath(service: str) -> str:
    return path.join(path.dirname(path.dirname(__file__)), f".auth-cache--{service}")


def english_join(items: List[str]) -> str:
    """
    Joins items in a sentence-compatible way, adding "and" at the end
    
    >>> english_join(["a", "b", "c"])
    'a, b and c'
    >>> english_join(["a"])
    'a'
    >>> english_join(["a", "b"])
    'a and b'
    """
    if len(items) == 1:
        return items[0]
    return ", ".join(items[: len(items) - 1]) + " and " + items[len(items) - 1]


def print_dry_run(text: str):
    """
    Apply special formatting for dry-run specific messages
    """
    DRY_RUN_FMT = dye(" DRY RUN ", bg=0x333, fg=0xFFF) + dye("  {}", style="dim")
    print(DRY_RUN_FMT.format(text))


if __name__ == "__main__":
    import doctest

    doctest.testmod()
