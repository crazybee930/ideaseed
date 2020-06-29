"""Note down your ideas and get them to the right place, without switching away from your terminal

Usage: 
    ideaseed (--help | --about | --version | --config)
    ideaseed [options] [-t TAG...] [-l LABEL...] [-# LABEL...] [-@ USERNAME...] ARGUMENTS...

Examples:
    # Save a card "test" in schoolsyst/webapp > project "UX" > column "To-Do"
    $ ideaseed schoolsyst/webapp UX "test"
    # Save a card "lorem" in your-username/ipsum > project "ipsum" > column "To-Do"
    $ ideaseed ipsum "lorem"
    # Save a card "a CLI to note down ideas named ideaseed" in your user profile > project "incubator" > column "willmake"
    $ ideaseed --user-keyword=project --user-project=incubator project willmake "a CLI to note down ideas named ideaseed"

Arguments:
    REPO        Select a repository
                    If not given                        Uses Google Keep instead of GitHub (or uses your user profile's projects if --project is used)
                    If --user-keyword's value is given  Creates a card on your user's project (select which project with --user-project)
                    If given in the form OWNER/REPO     Uses the repository OWNER/REPO
                    If given in the form REPO           Uses the repository "your username/REPO"
    PROJECT     Select a project by name to put your card to [default: --default-project's value]
                    If creating a card on your user's project, this becomes the COLUMN
    COLUMN      Select a project's column by name [default: --default-column's value]
                    If creating a card on your user's project, this is ignored

Options:
    -c --color COLOR           Chooses which color to use for Google Keep cards. See Color names for allowed values.
    -t --tag TAG               Adds tags to the Google Keep card or labels to the GitHub issue (see --issue). Use it multiple times to set multiple tags.
    -i --issue                 Creates an issue for the card and link them together. IDEA becomes the issue's title, except if --title is specified,
                               in which case IDEA becomes the issue's description and --title's value the issue title.
    (WIP) -I --interactive     Prompts you for the above options when they are not provided.
    -T --title TEXT            Sets the Google Keep card's title. When used with --issue, sets the issue's title.
    -L --logout                Clears the authentification cache
    -m --create-missing        Create non-existant tags, labels, projects or columns specified, upon confirmation.
    -o --open                  Open the relevant URL in your web browser.
    -l --label LABEL           Alias for --tag. See --tag's description.
    -# --label LABEL           Just another shorthand for --label.
    -@ --assign-to USERNAME    Assigns users to the created issue. Only works when --issue is used.
    -M --milestone TITLE       Assign the issue to a milestone with title TITLE.
       --pin                   Pin Google Keep cards
       --dry-run               Don't actually affect websites, put print what it would've done. Still logs in. Beware, --create-missing ignores this flag and still creates missing objects.
       --about                 Details about ideaseed like currently-installed version
       --config                Easily configure your ideaseed and create your alias.
       --version               Like --about, without dumb and useless stuff

Settings options: It's comfier to set these in your alias (run `ideaseed --config`)
       --user-project NAME     Name of the project to use as your user project
       --user-keyword NAME     When REPO is NAME, creates a GitHub card on your user profile instead of putting it on REPO
       --no-auth-cache         Don't save credentials in a temporary file at {cache_filepath}
       --no-check-for-updates  Don't check for updates, don't prompt to update when current version is outdated
       --no-self-assign        Don't assign the issue to yourself
    
    Options beginning with --default can refer to some dynamic information using %(placeholder)s.
    Available placeholders:
        repository - the repository's name
        owner      - the repository's owner
        username   - the username of which account you are using ideaseed with
        project    - the selected project's name (only available to --default-column)
    
       --default-column NAME   Set the default column name. [default: To Do]
       --default-project NAME  Set the default project name. [default: %(repository)s]
       

Color names: Try with the first letter only too
    blue, brown, darkblue, gray, green, orange, pink, purple, red, teal, white, yellow
    Some color have aliases:
    - cyan is the same as teal
    - indigo is the same as darkblue
    - grey is the same as gray
    - magenta is the same as purple
"""

from ideaseed.update_checker import get_latest_version
from ideaseed import update_checker, config_wizard
from ideaseed.gkeep import push_to_gkeep
from ideaseed.github import clear_auth_cache, push_to_repo, push_to_user
from typing import *
from colr import docopt
from pprint import pprint
from ideaseed.utils import ask, dye, get_token_cache_filepath
from ideaseed.constants import (
    COLOR_ALIASES,
    COLOR_NAME_TO_HEX_MAP,
    VALID_COLOR_NAMES,
    VERSION,
)
from ideaseed.dumb_utf8_art import ABOUT_SCREEN
import cli_box as box
from inquirer import Confirm
import subprocess
import sys


def run(argv=None):
    args = resolve_arguments(
        docopt(
            __doc__.format(cache_filepath=get_token_cache_filepath("*")),
            argv,
            script="ideaseed",
        )
    )
    validate_argument_presence(args)

    args["--tag"] += args["--label"]
    # Remove duplicate tags
    args["--tag"] = list(
        set(args["--tag"])
    )  # XXX: We're loosing order of elements here.

    if not args["--no-check-for-updates"]:
        latest_version = get_latest_version()
        if latest_version > VERSION:
            print(update_checker.notification(VERSION, latest_version))
            if update_checker.prompt(VERSION, latest_version):
                update_checker.upgrade(latest_version)
                print(f"Re-running your command with ideaseed v{latest_version}...")
                print("Running " + " ".join(sys.argv))
                subprocess.run(sys.argv)
                return

    if args["--dry-run"]:
        print(
            dye(
                f"\n============ Running in {dye('dry run', style='bold', fg=0xfff)} {dye('mode ============', style='dim')}\n",
                style="dim",
            )
        )

    if args["--about"]:
        print(ABOUT_SCREEN.format(version=VERSION))
        return

    if args["--config"]:
        config_wizard.run()
        return

    if args["--version"]:
        print(VERSION)
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


class ValidationError(Exception):
    pass


def validate_argument_presence(args: Dict[str, str]) -> None:
    """
    Raises a `ValidationError` if one of the arguments is not allowed based
    on the other arguments.
    """

    GOOGLE_KEEP_ONLY = ("--color",)
    GITHUB_ONLY = ("--issue",)
    GITHUB_ISSUE_ONLY = ("--milestone", "--assign-to")
    using_github = len(args["ARGUMENTS"]) > 1

    if using_github and not args["--issue"] and (args["--tag"] or args["--label"]):
        raise ValidationError(
            "--label (or --tag) can only be used with --issue or when creating"
            "a Google Keep card."
        )

    if not args["--issue"] and any(
        [v for k, v in args.items() if k in GITHUB_ISSUE_ONLY]
    ):
        raise ValidationError(
            "The following options only work when --issue is used: "
            + ", ".join(GITHUB_ISSUE_ONLY)
        )

    if using_github and any([v for k, v in args.items() if k in GOOGLE_KEEP_ONLY]):
        raise ValidationError(
            "The following options are not allowed when using GitHub: "
            + ", ".join(GOOGLE_KEEP_ONLY)
        )
    if not using_github and any([v for k, v in args.items() if k in GITHUB_ONLY]):
        raise ValidationError(
            "The following options are not allowed when using Google Keep: "
            + ", ".join(GITHUB_ONLY)
            + "\n"
            + "Maybe you've forgotten to specify a repository? (see ideaseed --help)"
        )


def expand_color_name(color: str) -> str:
    # Initialize the array of matches
    matching_color_names: List[str] = []
    # Filter `color_names` to only get the color names that start with `color`
    for color_name in VALID_COLOR_NAMES:
        if color_name.lower().startswith(color.lower()):
            matching_color_names += [color_name]
    # Resolve synonyms
    matching_color_names_resolved = matching_color_names
    for i, color_name in enumerate(matching_color_names):
        if color_name in COLOR_ALIASES.keys():
            matching_color_names_resolved[i] = COLOR_ALIASES[color_name]
    # Remove duplicates
    matching_color_names = list(set(matching_color_names))
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
