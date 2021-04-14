from __future__ import annotations

import shlex
from os import getenv, path
from os.path import isfile
from typing import Any, Optional, Union

from ideaseed.utils import answered_yes_to, ask


class UnknownShellError(Exception):
    """The current login shell is not known"""


def get_shell_name() -> str:
    """
    Gets the shell name.
    """
    executable_path = getenv("SHELL")
    if not executable_path:
        return ""
    shell_name = path.split(executable_path)[1]
    return shell_name


SHELL_NAMES_TO_RC_PATHS = {
    "fish": "~/.config/fish/config.fish",
    "bash": "~/.bashrc",
    "zsh": "~/.zshrc",
    "csh": "~/.cshrc",
    "ksh": "~/.kshrc",
    "tcsh": "~/.tcshrc",
}


def reverse_docopt(program_name: str, args_map: dict[str, Any]) -> str:
    """
    Turns a docopt-style dict of arguments and flags into a string
    you would type into your shell (WIP)
    
    >>> reverse_docopt('prog', { '--ab': 4, '--bb': 'yes', '--cb': True, '--db': False, '--eb': ['5', 'fefez$$/./!**fe'], 'thingie': True, 'nothingie': False, 'SHOUT': ':thinking:' })
    "prog --ab --ab --ab --ab --bb=yes --cb --eb=5 --eb='fefez$$/./!**fe' thingie :thinking:"
    """
    line = [program_name]

    for key, value in args_map.items():
        # Arguments
        if not key.startswith("--"):
            # Strings in the command that are either present or not
            if type(value) is bool and value:
                line += [key]
            # Positional arguments
            elif type(value) is str:
                line += [value]
            continue
        # Flag with a value, but is not specified
        if value is None:
            continue
        # Flags with a value
        elif type(value) is str:
            line += [f"{key}={shlex.quote(value)}"]
        # Count (repeated value-less flag)
        elif type(value) is int:
            line += [key] * value
        # list (repeated flag with value)
        elif type(value) is list:
            line += [f"{key}={shlex.quote(str(v))}" for v in value]
        # Boolean (value-less flag, ony present if `True`)
        elif type(value) is bool and value:
            line += [key]

    return " ".join(line)


def get_alias_command(args_map: dict[str, Any], shortcut_name: str) -> str:
    """
    Returns the alias line, sth. like `idea='ideaseed --opt=value --opt2'`, 
    where ``shortcut_name`` is the alias' equation's LHS (`'idea'` in the example above)
    ``args_map`` is a map of options, docopt-style:
    {
        '--option': 'value'
    }
    >>> get_alias_command({ '--ab': 4, '--bb': 'yes', '--cb': True, '--db': False, '--eb': ['5', 'fefez$$/./!**fe'], 'thingie': True, 'nothingie': False, 'SHOUT': ':thinking:' }, 'idea')
    "alias idea='ideaseed --ab --ab --ab --ab --bb=yes --cb --eb=5 --eb=\\\\'fefez$$/./!**fe\\\\' thingie :thinking:'"
    """
    # nested shlex.quote gives completely bonkers output, adding '"'" to each side of a deeply-quoted string (the fezfez... here, for example)
    shortcut = reverse_docopt("ideaseed", args_map).replace("'", "\\'")
    return f"alias {shortcut_name}='{shortcut}'"


def write_alias_to_rc_file(shell_name: str, alias_line: str):
    supported_shells = list(SHELL_NAMES_TO_RC_PATHS.keys())
    if shell_name not in supported_shells:
        raise UnknownShellError()

    rcfile_path = path.expandvars(path.expanduser(SHELL_NAMES_TO_RC_PATHS[shell_name]))
    if not isfile(rcfile_path):
        err = FileNotFoundError()
        err.filename = rcfile_path
        raise err

    with open(rcfile_path, "a") as file:
        print(f"Appending the following to {rcfile_path}:\n\n  {alias_line}\n")
        file.writelines([alias_line + "\n"])
        print(
            "Restart your shell or source the file for the new alias to take effect, or execute the 'alias' line above"
        )


def prompt_for_settings() -> tuple[dict[str, str], str]:
    """
    Return type: (settings, shortcut_name)
    """

    settings: dict[str, Any] = {}

    settings["--auth-cache"] = (
        ask("Path to the authentification cache (leave blank to not use any)")
        or "<None>"
    )
    settings["--check-for-updates"] = answered_yes_to("Check for updates?")
    settings["--self-assign"] = answered_yes_to(
        "Assign yourself to issues if you don't assign anyone with -@ ?"
    )

    print(
        """
        For the two following questions, you can use {placeholders}.
        See https://github.com/ewen-lbh/ideaseed#placeholders
        for the full list of available placeholders.
        """.strip()
    )

    settings["--default-project"] = ask("Enter the default value for the project name")
    settings["--default-column"] = ask("Enter the default value for the column name")

    return (
        settings,
        ask(
            "What name do you want to invoke your configured ideaseed with? (a good one is 'idea')"
        ),
    )


def run():
    settings, shortcut_name = prompt_for_settings()
    alias_command = get_alias_command(settings, shortcut_name)
    shell_name = get_shell_name()
    try_adding_manually_message = f"""\
Try adding the following command to whatever file your shell runs every time it starts:

    {alias_command}

"""
    try:
        write_alias_to_rc_file(shell_name, alias_command)
    except UnknownShellError:
        print(f"Hmm... Seems like I don't know your shell, {shell_name!r}.")
        print(try_adding_manually_message)
        return
    except FileNotFoundError as error:
        print(f"File {error.filename!r} not found.")
        print(try_adding_manually_message)
