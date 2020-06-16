from ideaseed.constants import COLOR_NAME_TO_HEX_MAP, C_PRIMARY
import json
import webbrowser
from os import path
from ideaseed.utils import ask, dye, get_token_cache_filepath
from typing import *
from inquirer import Text, Password, Confirm
from gkeepapi import Keep
from gkeepapi.exception import LoginException
from gkeepapi.node import ColorValue
import sys


def write_to_cache(keep: Keep, email: str) -> None:
    with open(get_token_cache_filepath("gkeep"), "w", encoding="utf8") as file:
        json.dump({"master_token": keep.getMasterToken(), "email": email}, file)


def login_from_cache() -> Optional[Keep]:
    if not path.exists(get_token_cache_filepath("gkeep")):
        return None

    with open(get_token_cache_filepath("gkeep"), encoding="utf8") as file:
        creds = json.load(file)

    keep = Keep()
    keep.resume(email=creds["email"], master_token=creds["master_token"])
    return keep


def login(args: Dict[str, Any]) -> Keep:
    # Try to log in from cache
    keep = login_from_cache()
    if keep is not None:
        return keep
    else:
        del keep

    # Ask for creds
    username, password = ask(
        Text("u", message="E-mail"), Password("p", message="Password")
    )

    # Log in
    keep = Keep()
    try:
        keep.login(username, password)
        write_to_cache(keep, username)
    except LoginException as error:
        # Handle errors...
        (topic, message) = error.args
        if topic == "BadAuthentification":
            print(dye("Bad credentials", fg=0xF00))
            return login(args)
        elif topic == "NeedsBrowser":
            print(
                dye(
                    """You have two-step authentification set up, please add an App Password.
Go to https://myaccount.google.com/apppasswords,
Click on 'Generate', Choose a name and a device, then copy the code
and use it as your password.""",
                    fg=0xF00,
                )
            )
            sys.exit()
    return keep


def push_to_gkeep(args: Dict[str, Any]) -> None:
    # Log in
    print("Logging in...", end="")
    keep = login(args)
    print(" Done.")

    # Announce what we'll do
    color = args["--color"] or 'White'
    print(
        f"Creating a "
        + dye(' ' + color.lower() + ' ', fg=0x000, bg=COLOR_NAME_TO_HEX_MAP[color])
        + dye(f" Google Keep card with tags {', '.join(args['--tag'])}", fg=C_PRIMARY)
    )

    # Create the note
    note = keep.createNote(title=args["--title"], text=args["IDEA"])
    note.color = getattr(ColorValue, color)
    note.pinned = True

    # Find/create all the labels
    all_tags = keep.labels()
    for tag in args["--tag"]:
        label = keep.findLabel(tag)
        if label is None and args["--create-missing"]:
            if ask(Confirm("ans", f"Create missing tag {tag!r}?")):
                label = keep.createLabel(tag)
        elif label is None:
            print(dye(f"Error: Tag {tag!r} not found", fg=0xF00))
        note.labels.add(label)

    # Beam it up to Google's servers
    keep.sync()
    
    # Open the browser
    if args['--open']:
        url = f"https://keep.google.com/u/0/#NOTE/{note.id}"
        webbrowser.open(url)
