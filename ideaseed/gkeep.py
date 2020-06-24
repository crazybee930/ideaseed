from ideaseed.dumb_utf8_art import make_google_keep_art
from ideaseed.constants import COLOR_NAME_TO_HEX_MAP, C_PRIMARY
import json
import webbrowser
from os import path
from ideaseed.utils import (
    ask,
    dye,
    error_message_no_object_found,
    get_token_cache_filepath,
    print_dry_run,
)
from typing import *
from inquirer import Text, Password, Confirm
from gkeepapi import Keep
from gkeepapi.exception import LoginException, APIException
from gkeepapi.node import ColorValue
import sys
import cli_box


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
    print("🔑 Logging in...")
    sys.stdout.flush()
    # Handle API errors
    try:
        keep = login(args)
    except APIException as error:
        print("❌ Error with the Google Keep API")
        if error.code == 429:
            print(
                """Too much requests per minute. Try again later.
Don't worry, your idea is still safe,
just up-arrow on your terminal to re-run the command :)"""
            )
        print(dye(error, style="dim"))
        return
    print("✅ Logged in.")

    color = args["--color"] or "White"
    note = None

    # Find/create all the labels
    labels = []
    for tag in args["--tag"]:
        label = keep.findLabel(tag)
        if label is None and args["--create-missing"]:
            if ask(Confirm("ans", message=f"Create missing tag {tag!r}?")):
                label = keep.createLabel(tag)
        elif label is None:
            print(error_message_no_object_found("tag", tag))
            return
        labels += [label]

    # Create the card
    if not args["--dry-run"]:
        note = keep.createNote(title=args["--title"], text=args["IDEA"])
        note.color = getattr(ColorValue, color)
        note.pinned = args["--pin"]
        url = f"https://keep.google.com/u/0/#NOTE/{note.id}"
        for label in labels:
            note.labels.add(label)
    else:
        print_dry_run(
            f"note = keep.createNote(title={args['--title']!r}, text={args['IDEA']!r})"
        )
        print_dry_run(f"note.color = getattr(ColorValue, {color!r})")
        print_dry_run(f"note.pinned = {args['--pin']!r}")
        url = "N/A"
        for label in labels:
            print_dry_run(f"note.labels.add({label!r})")

    # Announce created card
    print(
        make_google_keep_art(
            url=url,
            title=args["--title"],
            pinned=args["--pin"],
            tags=args["--tag"],
            body=args["IDEA"],
            color=args["--color"],
        )
    )

    # Beam it up to Google's servers
    keep.sync()

    # Open the browser
    if args["--open"] and not args["--dry-run"]:
        webbrowser.open(url)
