from __future__ import annotations

import json
import sys
import webbrowser
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Optional, Tuple, Union

import gkeepapi
import gkeepapi.node
import rich.traceback
from gkeepapi import Keep
from gkeepapi.exception import APIException, LoginException
from gkeepapi.node import ColorValue
from rich import print

from ideaseed import authentication, ui
from ideaseed.constants import (COLOR_ALIASES, COLOR_NAME_TO_HEX_MAP,
                                VALID_COLOR_NAMES)
from ideaseed.utils import (answered_yes_to, ask, case_insensitive_find,
                            error_message_no_object_found, print_dry_run)

rich.traceback.install()


class AuthCache(authentication.Cache):
    def __init__(self, path: Path):
        super().__init__(path=path, service="google_keep")

    def login_manually(
        self,
        username: Optional[str] = None,
        password: Optional[str] = None,
        entering_app_password: bool = False,
    ) -> Tuple[Keep, dict[str, Any]]:
        # Ask for creds
        if not username:
            username = ask("Email")
        if not password:
            password = ask(
                "App password" if entering_app_password else "Password", password=True
            )

        # Log in
        keep = Keep()

        try:
            keep.login(username, password)

            # elif keyring:
            #     service, name =
        except LoginException as error:
            # Handle errors...
            topic, _ = error.args
            if topic == "BadAuthentication":
                print("[red]Bad credentials")
                return self.login_manually()
            elif topic == "NeedsBrowser":
                print(
                    """[red]You have two-step authentification set up, please add an App Password.
    Go to https://myaccount.google.com/apppasswords (a tab should've been opened)""",
                )
                webbrowser.open("https://myaccount.google.com/apppasswords")
                try:
                    return self.login_manually(
                        username=username, entering_app_password=True
                    )
                except RecursionError:
                    print("Too much attempts.")
                    sys.exit()
            else:
                print(topic)
                sys.exit()
        return keep, {"master_token": keep.getMasterToken(), "email": username,}

    def login_from_cache(self) -> Optional[Keep]:
        try:
            keep = Keep()
            keep.resume(**self.cache)
            return keep
        except LoginException:
            return None


@contextmanager
def handle_api_errors():
    try:
        yield
    except APIException as error:
        print("Error with the Google Keep API")
        if error.code == 429:
            print(
                """Too much requests per minute. Try again later.
Don't worry, your idea is still safe,
just up-arrow on your terminal to re-run the command :)"""
            )
        print(f"[dim]{error}[/]")
        return


def find_and_create_labels(
    keep: Keep, labels: list[str], create_missing: bool
) -> list[gkeepapi.node.Label]:
    labels = []
    for label in labels:
        label = keep.findLabel(label)
        if label is None:
            if create_missing:
                if answered_yes_to(f"Create missing label {label!r}?"):
                    label = keep.createLabel(label)
            else:
                print(error_message_no_object_found("label", label))
                return []

        if label:
            labels += [label]
    return labels


def push_to_gkeep(
    color: str,
    label: list[str],
    create_missing: bool,
    dry_run: bool,
    title: Optional[str],
    body: str,
    pin: bool,
    assign: list[str],
    open: bool,
    auth_cache: Optional[str],
    **_,
) -> None:

    # Get correct color name casing
    color = case_insensitive_find(VALID_COLOR_NAMES, color)
    # Resolve color aliases
    if color in COLOR_ALIASES.keys():
        color = COLOR_ALIASES[color]

    # Log in
    sys.stdout.flush()
    # Handle API errors
    with handle_api_errors():
        keep = AuthCache(Path(auth_cache)).login()

    # Find/create all the labels
    labels = find_and_create_labels(keep, label, create_missing=create_missing)

    # Create the card
    if not dry_run:
        note = create_card(
            keep,
            assign=assign,
            color=color,
            labels=labels,
            pin=pin,
            title=title,
            body=body,
        )

    url = f"https://keep.google.com/u/0/#NOTE/{note.id}" if not dry_run else None

    # Announce created card
    ui.show(
        title=title or "",
        right_of_title="pinned" if pin else "",
        description=body,
        labels=map(to_ui_label, labels),
        card_title="",
        card_style=to_rich_color(color) + " on black",
        milestone=None,
        assignees=assign,
        project=None,
        project_column=None,
        url=url,
    )

    # Beam it up to Google's servers
    keep.sync()

    # Open the browser
    if open and not dry_run:
        webbrowser.open(url)


def create_card(
    keep: Keep,
    assign: list[str],
    color: str,
    labels: list[gkeepapi.node.Label],
    pin: bool,
    title: str,
    body: str,
) -> gkeepapi.node.Note:
    note = keep.createNote(title=title, text=body)
    note.color = getattr(ColorValue, color)
    note.pinned = pin
    for label in labels:
        note.labels.add(label)
    for email in assign:
        note.collaborators.add(email)


def to_ui_label(label: gkeepapi.node.Label) -> ui.Label:
    return ui.Label(name=label.name, url=f"https://keep.google.com/#label/{label.name}")


def to_rich_color(color: str) -> str:
    return (
        "#" + COLOR_NAME_TO_HEX_MAP[color]
        if color in COLOR_NAME_TO_HEX_MAP
        else "default"
    )


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
