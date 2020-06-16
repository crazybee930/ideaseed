"""Note down your ideas and get them to the right place, without switching away from your terminal

Usage: 
    ideaseed (--help | --about | --version)
    ideaseed [options] [-t TAG...] ARGUMENTS...

Examples:
    # Save a card "test" in schoolsyst/webapp > project "UX" > column "To-Do"
    $ ideaseed schoolsyst/webapp UX "test"
    # Save a card "lorem" in your-username/ipsum > project "ipsum" > column "To-Do"
    $ ideaseed ipsum "lorem"
    # Save a card "a CLI to note down ideas named ideaseed" in your user profile > project "incubator" > column "willmake"
    $ ideaseed --user-keyword=project --user-project=incubator project "a CLI to note down ideas named ideaseed"

Arguments:
    REPO        Select a repository
                    If not given                        Uses Google Keep instead of GitHub (or uses your user profile's projects if --project is used)
                    If --user-keyword's value is given  Creates a card on your user's project (select which project with --user-project)
                    If given in the form OWNER/REPO     Uses the repository OWNER/REPO
                    If given in the form REPO           Uses the repository "your username/REPO"
    PROJECT     Select a project by name to put your card to [default: REPO's value]
                    If creating a card on your user's project, this becomes the COLUMN
    COLUMN      Select a project's column by name [default: To do]
                    If creating a card on your user's project, this is ignored

Options:
    -c --color COLOR        Chooses which color to use for Google Keep cards. See Color names for allowed values.
    -t --tag TAG            Adds tags to the Google Keep card. Use it multiple times to set multiple tags.
                            When used together with --issue, --tag means labels.
    -i --issue              Creates an issue for the card and link them together. IDEA becomes the issue's title, except if --title is specified,
                            in which case IDEA becomes the issue's description and --title's value the issue title.
    (WIP) -I --interactive  Prompts you for the above options when they are not provided.
    -T --title TEXT         Sets the Google Keep card's title. When used with --issue, sets the issue's title.
    -L --logout             Clears the authentification cache
    -m --create-missing     Create non-existant tags, labels, projects or columns specified, upon confirmation.
       --about              Details about ideaseed like currently-installed version
       --version            Like --about, without dumb and useless stuff

Settings options: It's comfier to set these in your alias, e.g. alias idea="ideaseed --user-project=incubator --user-keyword=project --no-auth-cache --create-missing"
       --user-project NAME  Name of the project to use as your user project
       --user-keyword NAME  When REPO is NAME, creates a GitHub card on your user profile instead of putting it on REPO
       --no-auth-cache      Don't save credentials in a temporary file at {cache_filepath}

Color names: Try with the first letter only too
    blue, brown, darkblue, gray, green, orange, pink, purple, red, teal, white, yellow
"""

from ideaseed.gkeep import push_to_gkeep
from ideaseed.github import clear_auth_cache, push_to_repo, push_to_user
from typing import *
from docopt import docopt
from pprint import pprint
from ideaseed.utils import dye, get_token_cache_filepath
from ideaseed.constants import COLOR_NAME_TO_HEX_MAP
from ideaseed.dumb_utf8_art import DUMB_UTF8_ART


def run(argv=None):
    args = resolve_arguments(
        docopt(__doc__.format(cache_filepath=get_token_cache_filepath("*")), argv)
    )
    validate_argument_presence(args)
    args = resolve_arguments_defaults(args)

    if args["--about"]:
        print(DUMB_UTF8_ART.format(version="0.1.0"))
        return

    if args["--version"]:
        print("0.1.0")
        return

    if args["--color"]:
        args["--color"] = expand_color_name(args["--color"])

    if args["--logout"]:
        clear_auth_cache()

    if args["REPO"]:
        if args["REPO"] == args["--user-keyword"]:
            push_to_user(args)
        else:
            push_to_repo(args)
    else:
        push_to_gkeep(args)


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


def resolve_arguments_defaults(args: Dict[str, Any]) -> Dict[str, Any]:
    return {
        **args,
        "PROJECT": args["PROJECT"] or args["REPO"],
        "COLUMN": args["COLUMN"] or "To do",
    }


class ValidationError(Exception):
    pass


def validate_argument_presence(args: Dict[str, str]) -> None:
    """
    Raises a `ValidationError` if one of the arguments is not allowed based
    on the other arguments.
    """

    GOOGLE_KEEP_ONLY = ("--color", "--tag")
    GITHUB_ONLY = ("--issue",)
    using_github = len(args["ARGUMENTS"]) > 1

    if using_github and any([v for k, v in args.items() if k in GOOGLE_KEEP_ONLY]):
        raise ValidationError(
            "The following options are not allowed when using GitHub: "
            + ", ".join(GOOGLE_KEEP_ONLY)
            + f"\n{args!r}"
        )
    if not using_github and any([v for k, v in args.items() if k in GITHUB_ONLY]):
        raise ValidationError(
            "The following options are not allowed when using Google Keep: "
            + ", ".join(GITHUB_ONLY)
        )


def expand_color_name(color: str) -> str:
    # All possible color names
    color_names = [k for k in COLOR_NAME_TO_HEX_MAP.keys()]
    # Initialize the array of matches
    matching_color_names: List[str] = []
    # Filter `color_names` to only get the color names that start with `color`
    for color_name in color_names:
        if color_name.lower().startswith(color.lower()):
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
