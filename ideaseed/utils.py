from typing import Optional
from typing import *
import colr
from emoji import emojize
import inquirer
from os import path
from random import randint
import re


def dye(
    text: str,
    fg: Union[int, str, None] = None,
    bg: Union[int, str, None] = None,
    style: Optional[str] = None,
    no_closing: bool = False,
):
    return colr.color(
        text=text,
        fore=f"{fg:x}" if type(fg) is int else fg,
        back=f"{bg:x}" if type(bg) is int else bg,
        style=style,
        no_closing=no_closing,
    )


def readable_text_color_on(
    background: str, light: str = "FFFFFF", dark: str = "000000"
) -> str:
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


def hex_to_rgb(hexstring: Union[str, int]) -> Tuple[int, int, int]:
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


def error_message_no_object_found(objtype: str, objname: str) -> str:
    return (
        dye(f"Error: missing {objtype} {objname!r}", fg=0xF00,)
        + """
💡 Use --create-missing and ideaseed will ask you if you want to create missing 
labels, issues, projects, columns, milestones..."""
    )


def render_markdown(text: str) -> str:
    heading = re.compile(r"(#+)\s*(.+)")
    list_item = re.compile(r"(\s*)-\s*(.+)")
    image = re.compile(r"!\[(.+)\]\((.+)\)")
    code = re.compile(r"`([^`]+)`")
    em = re.compile(r"(?:_([^_].+[^_])_)|(?:\*([^*].+[^*])\*)")
    strong = re.compile(r"(?:__(.+)__)|(?:\*\*(.+)\*\*)")
    rendered = ""
    in_code_block = False
    for line in text.splitlines():
        if line.strip().startswith("```"):
            in_code_block = not in_code_block
            rendered += "\n"
            continue
        if in_code_block:
            rendered += " " * 2 + line + "\n"
            continue
        if heading.match(line):
            match = heading.search(line)
            rendered_line = dye(match.group(2), style="bold")
        elif list_item.match(line):
            match = list_item.search(line)
            rendered_line = match.group(1) + dye("• ", style="dim") + match.group(2)
        else:
            rendered_line = line
        rendered_line = image.sub(dye(r"(image: \1)", style="dim"), rendered_line)
        rendered_line = code.sub(dye(r" \1 ", bg=0xDEDEDE), rendered_line)
        rendered_line = emojize(rendered_line, use_aliases=True)
        rendered_line = strong.sub(dye(r"\1\2", style="bold"), rendered_line)
        rendered_line = em.sub(dye(r"\1\2", style="italic"), rendered_line)
        # rendered_line = link.sub(dye(r' (link: \1)', style="dim"), rendered_line)
        rendered += rendered_line + "\n"
    return rendered


if __name__ == "__main__":
    import doctest

    doctest.testmod()
