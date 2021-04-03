from __future__ import annotations

import json
import sys
import webbrowser
from pathlib import Path
from typing import Any, Optional, Union

import inquirer
from gkeepapi import Keep
from gkeepapi.exception import APIException, LoginException
from gkeepapi.node import ColorValue

from ideaseed.constants import (
    COLOR_ALIASES,
    C_PRIMARY,
    COLOR_NAME_TO_HEX_MAP,
    VALID_COLOR_NAMES,
)
from ideaseed.dumb_utf8_art import make_google_keep_art
from ideaseed.utils import (
    answered_yes_to,
    case_insensitive_find,
    dye,
    error_message_no_object_found,
    print_dry_run,
)


def write_to_cache(keep: Keep, email: str, cache_path: Path) -> None:
    cache = {}
    cache_path.parent.mkdir(exist_ok=True, parents=True)
    if cache_path.exists():
        cache = json.loads(cache_path.read_text(encoding="utf-8"))
    cache["keep"] = {"master_token": keep.getMasterToken(), "email": email}
    cache_path.write_text(json.dumps(cache), encoding="utf-8")


def login_from_cache(cache_path: Path) -> Optional[Keep]:
    if not cache_path.exists():
        return None

    creds = json.loads(cache_path.read_text(encoding="utf-8")).get("keep")
    if not creds:
        return None

    keep = Keep()
    keep.resume(email=creds["email"], master_token=creds["master_token"])
    return keep


def login(
    auth_cache: Optional[str],
    username: Optional[str] = None,
    password: Optional[str] = None,
    entering_app_password: bool = False,
    **_,
) -> Keep:
    # Try to log in from cache
    if auth_cache:
        keep = login_from_cache(Path(auth_cache))
    if keep is not None:
        return keep
    else:
        del keep

    # Ask for creds
    if not username:
        username = inquirer.text("E-mail")
    if not password:
        password = inquirer.password(
            "App password" if entering_app_password else "Password"
        )

    # Log in
    keep = Keep()
    try:
        keep.login(username, password)
        if auth_cache:
            write_to_cache(keep, username, cache_path=Path(auth_cache))
        # elif keyring:
        #     service, name =
    except LoginException as error:
        # Handle errors...
        topic, _ = error.args
        if topic == "BadAuthentication":
            print(dye("Bad credentials", fg=0xF00))
            return login(auth_cache)
        elif topic == "NeedsBrowser":
            print(
                dye(
                    """You have two-step authentification set up, please add an App Password.
Go to https://myaccount.google.com/apppasswords (a tab should've been opened)""",
                    fg=0xF00,
                )
            )
            webbrowser.open("https://myaccount.google.com/apppasswords")
            try:
                return login(auth_cache, username=username, entering_app_password=True)
            except RecursionError:
                print("Too much attempts.")
                sys.exit()
        else:
            print(topic)
            sys.exit()
    return keep


def push_to_gkeep(
    color: str,
    tag: list[str],
    create_missing: bool,
    dry_run: bool,
    title: Optional[str],
    body: str,
    pin: bool,
    assign: list[str],
    open: bool,
    auth_cache: Optional[str],
    keyring: Optional[str],
    **_,
) -> None:
    tags = tag
    # Get correct color name casing
    color = case_insensitive_find(VALID_COLOR_NAMES, color)
    # Resolve color aliases
    if color in COLOR_ALIASES.keys():
        color = COLOR_ALIASES[color]

    # Log in
    sys.stdout.flush()
    # Handle API errors
    print("Logging in...")
    try:
        keep = login(auth_cache, keyring)
    except APIException as error:
        print("Error with the Google Keep API")
        if error.code == 429:
            print(
                """Too much requests per minute. Try again later.
Don't worry, your idea is still safe,
just up-arrow on your terminal to re-run the command :)"""
            )
        print(dye(error, style="dim"))
        return
    print("Logged in.")

    note = None

    # Find/create all the labels
    labels = []
    for tag in tags:
        label = keep.findLabel(tag)
        if label is None and create_missing:
            if answered_yes_to(f"Create missing tag {tag!r}?"):
                label = keep.createLabel(tag)
        elif label is None:
            print(error_message_no_object_found("tag", tag))
            return
        labels += [label]

    # Create the card
    if not dry_run:
        note = keep.createNote(title=title, text=body)
        note.color = getattr(ColorValue, color)
        note.pinned = pin
        url = f"https://keep.google.com/u/0/#NOTE/{note.id}"
        for label in labels:
            note.labels.add(label)
        for email in assign:
            note.collaborators.add(email)
    else:
        print_dry_run(f"Create note with title {title!r} and text {body!r}")
        print_dry_run(f"Set its color to {color!r}")
        if pin:
            print_dry_run(f"Pin it")
        url = "N/A"
        for label in labels:
            print_dry_run(f"Add label {label!r}")

    # Announce created card
    print(
        make_google_keep_art(
            url=url,
            title=title,
            pinned=pin,
            tags=tags,
            body=body,
            color=color,
            collaborators=assign,
        )
    )

    # Beam it up to Google's servers
    keep.sync()

    # Open the browser
    if open and not dry_run:
        webbrowser.open(url)


if __name__ == "__main__":
    push_to_gkeep(
        "cyan",
        [],
        True,
        False,
        title="gkrep",
        body="mm",
        pin=False,
        assign=[],
        open=True,
        auth_cache="/home/ewen/.cache/ideaseed/auth.json",
        keyring=None,
    )
