"""Note down your ideas and get them to the right place, without switching away from your terminal
Usage:
    ideaseed [options] [-# TAG...] [-@ USER...] BODY
    ideaseed [options] [-# TAG...] [-@ USER...] TITLE BODY
    ideaseed [options] [-# TAG...] [-@ USER...] REPO TITLE BODY
    ideaseed [options] [-# TAG...] [-@ USER...] REPO PROJECT TITLE BODY
    ideaseed [options] [-# TAG...] [-@ USER...] REPO PROJECT COLUMN TITLE BODY
    ideaseed [options] [-# TAG...] [-@ USER...] user PROJECT COLUMN TITLE BODY
    ideaseed [options] [-# TAG...] [-@ USER...] user PROJECT TITLE BODY
    ideaseed [options] config
    ideaseed [options] logout
    ideaseed [options] login
    ideaseed [options] about | --about
    ideaseed [options] version | --version
    ideaseed [options] help | --help
    ideaseed [options] update


Commands:
    user                    Creates cards in your user's project. 
                            (see https://github.com/users/YOURUSERNAME/projects)
                            Flags --no-issue and --repo has no effects.
                            Flag --default-column still applies.
                            REPO is _not_ set to 'user'.
    config                  Configures an alias with Configuration flags through a series of questions.
    log(in/out)             Fills/Clears the auth cache (see --auth-cache).
                            Has no effect when used with --keyring.
    about                   Show information about ideaseed.
    version                 Outputs the version number
    update                  Check for updates. If any is available, shows the changelog. 
                            You can then decide to install the new version.


Arguments:
    BODY      Sets the note's body. Required.
    TITLE     Sets the title.
    REPO      The repository to put the issue/card into. Uses the format [USER/]REPO. 
              If USER/ is omitted, the currently-logged-in user's username is assumed.
              Omitting this argument entirely has the effect of creating a Google Keep card instead.
              When used without PROJECT, the card is added to the Default Project (see --default-project)
              If the Default Project is '<None>', it creates an issue without a project card.
    PROJECT   Specify which GitHub project to add the card to.
              When used without COLUMN, the card is added to the Default Column (see --default-column)
              Can use Placeholders
    COLUMN    Specify which column to use.
              Can use Placeholders.


Options:
    -I --no-issue           Only creates a project card, no issue is created.
                            Has no effect when used without a REPO
    -T --title=TITLE        Specifies TITLE
    -R --repo=REPO          Specifies REPOSITORY
    -P --project=PROJECT    Specifies PROJECT
    -C --column=COLUMN      Specifies COLUMN
    -# --tag=TAG...         Add tags (GitHub) or labels (Google Keep)
                            Can be specified multiple times.
    -o --open               Open the created card (or issue) in your $BROWSER.
       --dry-run            Tell what will happen but does not do it. Still logs you in.
                            Beware, objects created with --create-missing will
                            still be created.
    -m --create-missing     Creates missing objects (projects, columns, and labels/tags)
    -@ --assign=USER...     Assign USER to the created issue. 
                            Can be specified multiple times.
                            Cannot be used in the 'user' command.

    REPO only: 
       --self-assign        Assign the created issue to yourself. 
                            Has no effect when --assign is used.
    -M --milestone=NAME     Adds the issue to the milestone NAME.

    Google Keep only:
       --pin                Pins the card. 
       --color=COLOR        Sets the card's color. [default: white]
                            Available values: blue, brown, darkblue (or indigo), 
                            gray (or grey), green, orange, pink, purple (or magenta), 
                            red, teal (or cyan), white, yellow. 


Configuration:
   --default-column=COLUMN    Specifies the Default Column. 
                              Used when PROJECT is set but not COLUMN
                              Can use Placeholders.
   --default-project=PROJECT  Specifies the Default Project. 
                              Used when REPO is set but not PROJECT
                              Can use Placeholders.
                              If not set, or set to '<None>',
                              using REPO without PROJECT creates an issue
                              without its project card.
   --auth-cache=FILEPATH      Set the filepath for the auth. cache [default: $HOME/cache/ideaseed/auth.json]
                              If set to '<None>', disables caching of credentials.
                              Has no effect when used with --keyring.
   --check-for-updates        Check for new versions and show a notification if a new one is found.


Placeholders:
    {repository}      Replaced with the repository's name
    {owner}           Replaced with the repository's owner
    {username}        Replaced with the currently-logged-in GitHub user's username
    {project}         Replaced with the project the card will be added to.
                      Not available to --default-project or PROJECT.
"""


from __future__ import annotations

from typing import Any, Optional, Union
from pathlib import Path

from docopt import docopt

from ideaseed import config_wizard, update_checker, gkeep, github_cards
from ideaseed.constants import (
    VALID_COLOR_NAMES,
    VERSION,
)
from ideaseed.dumb_utf8_art import ABOUT_SCREEN
from ideaseed.update_checker import get_latest_version
from ideaseed.utils import english_join

__doc__ = __doc__.replace("$HOME", str(Path.home()))


class UsageError(Exception):
    pass


def run(argv=None):
    flags = docopt(__doc__, argv)
    args = flags_to_args(flags)
    args |= {"keyring": None}  # I'll add support for keyrings in another PR

    if args["keyring"] and args["auth_cache"]:
        args["auth_cache"] = None

    print(args)

    if args["color"] and args["color"] not in map(str.lower, VALID_COLOR_NAMES):
        raise UsageError(
            f"{args['color']!r} is not a valid color name. Valid color names are {english_join(map(str.lower, VALID_COLOR_NAMES))}"
        )

    if args["check_for_updates"]:
        latest_version = get_latest_version()
        if latest_version > VERSION:
            print(update_checker.notification(VERSION, latest_version))

    # Handle defaults


    if args["about"]:
        print(ABOUT_SCREEN.format(version=VERSION))
    elif args["version"]:
        print(VERSION)
    elif args["help"]:
        print(__doc__)
    elif args["update"]:
        update_checker.check_and_prompt()
    elif args["config"]:
        config_wizard.run()
    elif args["login"]:
        print("Logging into Google Keep:")
        gkeep.login(**args)
        print("Logging into GitHub:")
        github_cards.login(**args)
    elif args["logout"]:
        if args["auth_cache"] is None:
            # print("No cache to clear (remove --keyring or set --auth-cache to not '<None>')")
            print("No cache to clear")
        else:
            Path(args["auth_cache"]).unlink(missing_ok=True)
            print("Cache cleared.")
    elif args["user"]:
        github_cards.push_to_user(**args)
    elif args["repo"]:
        github_cards.push_to_repo(**args)
    else:
        gkeep.push_to_gkeep(**args)

def flags_to_args(flags: dict[str, Any]) -> dict[str, Any]:
    """
    Turn flags dict from docopt into **kwargs-usable dict.
    '--'-prefix is removed, dashes are turned into underscores 
    and keys are lowercased.
    When conflicts arise (ie --repo: None vs REPO: "ideaseed"), do a 'or',
    prefering values appearing sooner in the dict.
    Also replaces `'<None>'` with `None`

    >>> flags_to_args({'--about': False,
    ... '--assign': None,
    ... '--auth-cache': '~/.cache/ideaseed/auth.json',
    ... '--create-missing': False,
    ... '--default-project': '<None>',
    ... '--tag': None,
    ... '--title': None,
    ... '--version': False,
    ... 'BODY': 'b',
    ... 'COLUMN': None,
    ... 'REPO': None,
    ... 'TITLE': 'a',
    ... 'version': True})
    {'about': False, 'assign': None, 'auth_cache': '~/.cache/ideaseed/auth.json', 'create_missing': False, 'default_project': None, 'tag': None, 'title': 'a', 'version': True, 'body': 'b', 'column': None, 'repo': None}
    """
    args = {}
    for name in flags.keys():
        if flags[name] == "<None>":
            flags[name] = None
        normalized_name = name.removeprefix("--").replace("-", "_").lower()
        if normalized_name in args.keys():
            args[normalized_name] = args[normalized_name] or flags[name]
        else:
            args[normalized_name] = flags[name]
    return args
