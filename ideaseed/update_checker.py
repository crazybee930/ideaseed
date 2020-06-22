from typing import *
from ideaseed.constants import C_PRIMARY, RELEASES_RSS_URL
from xml.dom.minidom import parseString as parse_xml
import cli_box
import requests
from ideaseed.utils import ask, dye
import inquirer as q
from semantic_version import Version
import subprocess
import re


def get_latest_version() -> Version:
    raw_rss = requests.get(RELEASES_RSS_URL).text
    rss = parse_xml(raw_rss)
    version = (
        rss.childNodes[0]
        .getElementsByTagName("channel")[0]
        .getElementsByTagName("item")[0]
        .getElementsByTagName("title")[0]
        .childNodes[0]
        .nodeValue
    )
    return Version(version)


def get_changelog_heading_anchor(release_notes: str, upgrade_to: Version) -> str:
    """
    Get the changelog heading anchor for github.
    >>> get_changelog_heading_anchor(Version('0.8.0'))
    '080---2020-06-20'
    """
    pattern = re.compile(r"## \[" + str(upgrade_to) + r"\] - (.+)")
    date = pattern.search(release_notes).group(1)
    return f"{str(upgrade_to).replace('.', '')}---{date}"


def get_release_notes() -> str:
    return requests.get(
        "https://raw.githubusercontent.com/ewen-lbh/ideaseed/master/CHANGELOG.md"
    ).text


def get_release_notes_for_version(release_notes: str, version: Version) -> str:
    in_target_version = False
    ret = ""
    for line in release_notes.split("\n"):
        if line.startswith(f"## [{version}]"):
            in_target_version = True
            continue  # Don't add the actual heading to the release notes for this version
        # If the line is the start of another version's section, set to false
        elif line.startswith(f"##") and not line.startswith("###"):
            in_target_version = False

        if in_target_version:
            ret += line + "\n"
    return ret


def get_release_notes_link(release_notes: str, upgrade_to: Version) -> str:
    anchor = get_changelog_heading_anchor(release_notes, upgrade_to)
    return f"https://github.com/ewen-lbh/ideaseed/tree/master/CHANGELOG.md#{anchor}"


def notification(upgrade_from: Version, upgrade_to: Version) -> str:
    return cli_box.rounded(
        f"""==== Update available! ====

A new version of ideaseed is available for download:
{upgrade_from} -> {upgrade_to}
"""
    )


def render_markdown(text: str) -> str:
    heading = re.compile(r"(#+)\s*(.+)")
    list_item = re.compile(r"(\s*)-\s*(.+)")
    image = re.compile(r"!\[(.+)\]\((.+)\)")
    code = re.compile(r"`([^`]+)`")
    # link = re.compile(r'\[(.+)\]\((.+)\)')
    rendered = ""
    for line in text.splitlines():
        if heading.match(line):
            match = heading.search(line)
            rendered_line = dye(match.group(2), style="bold")
        elif list_item.match(line):
            match = list_item.search(line)
            rendered_line = match.group(1) + dye("• ", style="dim") + match.group(2)
        else:
            rendered_line = line
        rendered_line = image.sub(dye(r"(image: \1)", style="dim"), rendered_line)
        rendered_line = code.sub(dye(r" \1 ", bg=0xDEDEDE), rendered_line)
        # rendered_line = link.sub(dye(r' (link: \1)', style="dim"), rendered_line)
        rendered += rendered_line + "\n"
    return rendered


def prompt(upgrade_to: Version) -> bool:
    """
    Returns ``True`` if the user wants to upgrade, ``False`` otherwise.
    """
    answer = ask(
        q.List(
            "ans",
            message=f"Upgrade to v{upgrade_to} now?",
            choices=["Yes", "What has changed?", "No"],
        )
    )
    if answer == "What has changed?":
        release_notes = get_release_notes()
        url = get_release_notes_link(release_notes, upgrade_to)
        notes = get_release_notes_for_version(release_notes, upgrade_to)
        print(
            f"""\
Release notes for v{upgrade_to}
===============================

{render_markdown(notes).strip()}

---------------------------------------------
To see images, you can also read this online:
{url}
"""
        )
        return ask(q.Confirm("ans", message="Upgrade now?"))
    else:
        return answer == "Yes"


def upgrade(upgrade_to: Version):
    cmd = ["pip", "install", "--upgrade", f"ideaseed=={upgrade_to}"]
    print(f"Running {' '.join(cmd)}...")
    subprocess.run(cmd)
