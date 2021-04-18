from __future__ import annotations

from random import randint
from typing import Any, Callable, Iterable, Optional, Text, Union

from rich import print
from rich.console import Console
from rich.prompt import (Confirm, DefaultType, InvalidResponse, Prompt,
                         PromptType)
from rich.text import TextType


class BetterPrompt(Prompt):
    """
    Provides a nicer way to select from a *dict* of choices that maps aliases to descriptions,
    so that the user doesn't have to type out the full option when choosing.

    Would like to implement a list of radio buttons like enquirer does,
    but that is way more difficult.
    """

    choices: Union[list[str], dict[str, str], None]

    def __init__(
        self,
        prompt: TextType,
        *,
        console: Console,
        password: bool,
        choices: Union[list[str], dict[str, str]],
        show_default: bool,
        show_choices: bool,
    ) -> None:
        super().__init__(
            prompt=prompt,
            console=console,
            password=password,
            choices=choices,
            show_default=show_default,
            show_choices=show_choices,
        )

    def check_choice(self, value: str) -> bool:
        assert self.choices is not None
        if isinstance(self.choices, list):
            return super().check_choice(value)
        else:
            return value.strip() in (
                set(self.choices.keys()) | set(self.choices.values())
            )

    def make_prompt(self, default: DefaultType) -> Text:
        prompt = self.prompt.copy()
        prompt.end = ""

        if self.show_choices and self.choices:
            if isinstance(self.choices, list):
                _choices = "/".join(self.choices)
            else:
                _choices = "/".join(f"{k}: {v}" for k, v in self.choices.items())
            choices = f"[{_choices}]"
            prompt.append(" ")
            prompt.append(choices, "prompt.choices")

        if (
            default != ...
            and self.show_default
            and isinstance(default, (str, self.response_type))
        ):
            prompt.append(" ")
            _default = self.render_default(default)
            prompt.append(_default)

        prompt.append(self.prompt_suffix)

        return prompt

    def process_response(self, value: str) -> PromptType:
        val = super().process_response(value)
        if isinstance(self.choices, dict):
            if val not in self.choices.values() and val in self.choices.keys():
                return self.choices[val]
        return val


def readable_on(background: str, light: str = "FFFFFF", dark: str = "000000") -> str:
    """
    Choses either ``light`` or ``dark`` based on the background color
    the text is supposed to be written on ``background`` (also given as an hex int)
    
    WARN: All the color strings must be exactly 6 digits long.
    
    >>> readable_on('FEFAFE')
    '000000'
    >>> readable_on('333333')
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


def ask(
    question: str,
    is_valid: Callable[[str], bool] = lambda _: True,
    choices: Optional[list[str]] = None,
    password=False,
    default="",
) -> str:
    answer = ""
    while True:
        answer = BetterPrompt.ask(
            question, password=password, choices=choices, default=default
        )
        try:
            if is_valid(answer):
                break
        except InvalidResponse as error:
            print(error.message)
    return answer


def answered_yes_to(question: str, default: bool = False) -> bool:
    return Confirm.ask(question, default=default)


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
        f"[red]Error: missing {objtype} {objname!r}"
        + """
TIP: Use --create-missing and ideaseed will ask you if you want to create missing labels, issues, projects, columns, milestones..."""
    )


def case_insensitive_find(haystack: Iterable[str], needle: str) -> Optional[str]:
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
