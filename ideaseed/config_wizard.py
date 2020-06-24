from os import getenv
from os import path
from os.path import isfile
from typing import *
from inquirer import Text, List, Confirm, prompt, text
import shlex


class UnknownShellError(Exception):
    pass


def get_shell_name() -> str:
    """
    Gets the shell name.
    Values are:
    - fish
    - bash
    - zsh
    - csh
    - ksh
    - tcsh
    - powershell
    - cmd
    """
    executable_path = getenv("SHELL")
    shell_name = path.split(executable_path)[1]
    return shell_name


SHELL_NAMES_TO_RC_PATHS = {
    "fish": "~/.config/fish/config.fish",
    "bash": "~/.bashrc",
    "zsh": "~/.zshrc",
    "csh": "~/.cshrc",
    "ksh": "~/.kshrc",
    "tcsh": "~/.tcshrc",
    "powershell": "$profile",
    "cmd": None,
}


def reverse_docopt(program_name: str, args_map: Dict[str, Any]) -> str:
    """
    Turns a docopt-style dict of arguments and flags into a string
    you would type into your shell (WIP)
    
    >>> reverse_docopt('prog', { '--ab': 4, '--bb': 'yes', '--cb': True, '--db': False, '--eb' ['5', 'fefez$$/./!**fe'], 'thingie': True, 'nothingie': False, 'SHOUT': ':thinking:' })
    'prog --ab --ab --ab --ab --bb=yes --cb --eb=5 --eb=5 --eb="fefez\\$\\$/./\\!\\*\\*fe" thingie :thinking:'
    """
    line: str = program_name

    for key, value in args_map.items():
        # Arguments
        if not key.startswith("--"):
            # Strings in the command that are either present or not
            if type(value) is bool and value:
                line += f" {key}"
            # Positional arguments
            elif type(value) is str:
                line += f" {value}"
            continue
        # Flag with a value, but is not specified
        if value is None:
            continue
        # Flags with a value
        elif type(value) is str:
            line += f" {key}={shlex.quote(value)}"
        # Count (repeated value-less flag)
        elif type(value) is int:
            line += f" {key}" * value
        # List (repeated flag with value)
        elif type(value) is list:
            for v in value:
                line += f" {key}={shlex.quote(str(v))}"
        # Boolean (value-less flag, ony present if `True`)
        elif type(value) is bool:
            if value:
                line += f" {key}"

    return line


def get_alias_command(args_map: Dict[str, Any], shortcut_name: str) -> str:
    """
    Returns the alias line, sth. like `idea='ideaseed --opt=value --opt2'`, 
    where ``shortcut_name`` is the alias' equation's LHS (`'idea'` in the example above)
    ``args_map`` is a map of options, docopt-style:
    {
        '--option': 'value'
    }
    """
    return (
        "alias "
        + shortcut_name
        + "="
        + shlex.quote(reverse_docopt("ideaseed", args_map))
    )


def write_alias_to_rc_file(shell_name: str, alias_line: str):
    supported_shells = list(SHELL_NAMES_TO_RC_PATHS.keys())
    if shell_name not in supported_shells:
        raise UnknownShellError()

    rcfile_path = SHELL_NAMES_TO_RC_PATHS[shell_name]
    if not isfile(rcfile_path):
        err = FileNotFoundError()
        err.filename = rcfile_path
        raise err

    with open(rcfile_path, "a") as file:
        print(f"Appending the following to {rcfile_path}: {alias_line}")
        file.writelines([alias_line])


def prompt_for_settings() -> Tuple[Dict[str, str], str]:
    """
    Return type: (settings, shortcut_name)
    """
    questions = [
        Text(
            "--user-project",
            message="What GitHub project do you use on your GitHub profile?",
        ),
        Text(
            "--user-keword",
            message="What 'repository' name do you want to type to tell ideaseed to use your GitHub user profile's project instead?",
        ),
        Confirm(
            "--no-auth-cache",
            message="Cache credentials?",  # TODO: store creds cache files in ~/.cache/ideaseed/auth instead
        ),
        Confirm("--no-check-for-updates", message="Check for updates?"),
        Confirm(
            "--no-self-assign",
            message="Assign yourself to issues if you don't assign anyone with -@ ?",
        ),
        Text(
            "--default-project",
            message="Enter the default value for the project name (You can use %(placeholders)s, see https://github.com/ewen-lbh/ideaseed#available-placeholders-for---default--options for the full list",
        ),
        Text(
            "--default-column",
            message="Enter the default value for the column name (You can use %(placeholders)s, see https://github.com/ewen-lbh/ideaseed#available-placeholders-for---default--options for the full list",
        ),
    ]

    settings: Dict[str, Any] = prompt(questions)

    # Reverse bool values for --no- flags
    settings = {k: (not v if k.startswith("--no-") else v) for k, v in settings.items()}

    return (
        settings,
        text(
            message="What name do you want to invoke your configured ideaseed with? (a good one is 'idea')"
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
