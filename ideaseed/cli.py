"""Note down your ideas and get them to the right place, without switching away from your terminal

Usage: 
    ideaseed (--help | --about | --version)
    ideaseed [options] ARGUMENTS...

Arguments:
    REPO        Select a repository
                    If not given                     Uses Google Keep instead of GitHub (or uses your user profile's projects if --project is used)
                    If given in the form OWNER/REPO  Uses the repository OWNER/REPO
                    If given in the form REPO        Uses the repository "your username/REPO"
    PROJECT     Select a project by name to put your card to [default: REPO's value]
    COLUMNS     Select a project's column by name [default: To-Do]

Options:
    -p --project         Creates a GitHub project on your user profile instead of a Google Keep card if REPO is not given
    -c --color COLOR     Chooses which color to use for Google Keep cards. Can be one of: "bl[ue]", "br[own]", "d[arkblue]", "gra[y]", "gre[en]", "o[range]", "pi[nk]", "pu[rple]", "r[ed]", "t[eal]", "w[hite]", "y[ellow]"
    -t --tag TAG         Adds tags to the Google Keep card. 
    -i --issue TITLE     Creates an issue with title TITLE.
    -I --interactive     Prompts you for the above options when they are not provided.
       --create-missing  Create non-existant tags, projects or columns specified (needs confirmation if -I is used)
       --about           Details about ideaseed like currently-installed version
       --version         Like --about, without dumb and useless stuff
"""

from typing import *
from docopt import docopt
from pprint import pprint
from ideaseed.utils import dye
from ideaseed.constants import COLOR_NAME_TO_HEX_MAP
from ideaseed.dumb_utf8_art import DUMB_UTF8_ART


def run(argv=None):
    args = resolve_arguments(docopt(__doc__, argv))

    if args["--about"]:
        print(DUMB_UTF8_ART.format(version="0.1.0"))
        return

    if args["--version"]:
        print("0.1.0")
        return

    if args["--color"]:
        args["--color"] = expand_color_name(args["--color"])
    validate_argument_presence(args)

    for name, color in COLOR_NAME_TO_HEX_MAP.items():
        print(dye(name, bg=color, fg=0x000))


def resolve_arguments(args: Dict[str, Any]) -> Dict[str, Any]:
    """
    Apparently required positional arguments must come first...
    So I'm resolving them by hand here.
    """
    positional_args = args["ARGUMENTS"]
    idea = repo = project = column = None
    if len(positional_args) == 1:
        idea = positional_args[0]
    if len(positional_args) == 2:
        repo, idea = positional_args
    if len(positional_args) == 3:
        repo, project, idea = positional_args
    if len(positional_args) >= 4:
        repo, project, column, idea = positional_args
    return {"REPO": repo, "PROJECT": project, "COLUMN": column, "IDEA": idea, **args}


class ValidationError(Exception):
    pass


def validate_argument_presence(args: Dict[str, str]) -> None:
    """
    Raises a `ValidationError` if one of the arguments is not allowed based
    on the other arguments.
    """

    GOOGLE_KEEP_ONLY = ("--color", "--tag")
    GITHUB_ONLY = ("--issue",)

    using_github = args["--project"] or args["REPO"]

    if using_github and any([v for k, v in args.items() if k in GOOGLE_KEEP_ONLY]):
        raise ValidationError(
            "The following options are not allowed when using GitHub: "
            + ", ".join(GOOGLE_KEEP_ONLY)
        )
    elif any([v for k, v in args.items() if k in GITHUB_ONLY]):
        raise ValidationError(
            "The following options are not allowed when using Google Keep: "
            + ", ".join(GITHUB_ONLY)
        )


def expand_color_name(color: str) -> Any:
    # All possible color names
    color_names = list(COLOR_NAME_TO_HEX_MAP.keys())
    # Initialize the array of matches
    matching_color_names: List[str] = []
    # Filter `color_names` to only get the color names that start with `color`
    for color_name in color_names:
        if color_name.startswith(color):
            matching_color_names += [color_name]
    # If we have exactly _one_ element of `color_names` that matches, we return the only
    # element: it's a match!
    if len(matching_color_names) == 1:
        return matching_color_names[0]
    # If we have multiple choices, the given color was ambiguous.
    if len(matching_color_names) > 1:
        matching_color_names_display: List[str] = []
        for matching_color_name in matching_color_names:
            matching_color_names_display += [
                dye(
                    matching_color_name,
                    fg=0x000,
                    bg=COLOR_NAME_TO_HEX_MAP[matching_color_name],
                )
            ]
        raise ValueError(
            f"Ambiguous color shorthand {color!r}, it could mean one of: "
            + ", ".join(matching_color_names_display)
        )
    # If we had an empty array, then the given color name was incorrect.
    raise ValueError(f"Unknown color {color}")
