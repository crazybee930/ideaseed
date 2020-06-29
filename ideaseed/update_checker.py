from typing import *
from ideaseed.constants import C_PRIMARY, RELEASES_RSS_URL
from xml.dom.minidom import parseString as parse_xml
import cli_box
import requests
from ideaseed.utils import ask, dye, render_markdown
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


def get_versions_list_from_release_notes(release_notes: str) -> List[Version]:
    # Declarations
    pattern = re.compile(
        r"\[Unreleased\]\: https\:\/\/github\.com\/ewen\-lbh\/ideaseed\/compare\/v\d+\.\d+\.\d+\.\.\.HEAD"
    )
    extract_version_pattern = re.compile(r"\[(\d+\.\d+\.\d+)\]: https://")
    version_strings: List[str] = []
    # Tracking varialbe
    in_links_section = False
    for line in release_notes.splitlines():
        # Line is [Unreleased]: https://..., which always begins the version list
        if pattern.match(line):
            in_links_section = True
            continue
        # Subsequent lines that are like [version]: https://... are those we get versions from
        if in_links_section and extract_version_pattern.match(line):
            version_strings += [extract_version_pattern.search(line).group(1)]
    # Parse into SemVer Version objects
    versions = [Version(v) for v in version_strings]
    # Sort them (from 0.0.0 to ∞.∞.∞)
    versions = sorted(versions, key=lambda v: v.precedence_key)
    return versions


def get_release_notes_between_versions(
    release_notes: str, version_from: Version, version_to: Version
) -> str:
    # Get every version ∈ (version_from, version_to]
    versions = [
        v
        for v in get_versions_list_from_release_notes(release_notes)
        if version_from < v <= version_to
    ]
    # Order by most recent first
    versions = reversed(versions)
    catd_release_notes = ""
    for version in versions:
        catd_release_notes += f"## {version}"
        catd_release_notes += get_release_notes_for_version(release_notes, version)
    return catd_release_notes


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



def prompt(upgrade_from: Version, upgrade_to: Version) -> bool:
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
        all_versions = get_versions_list_from_release_notes(release_notes)
        # If the version jump is more than one version, print concatednated release notes
        # so that the user can get all of the changes.
        # eg: i'm upgrading from 0.6.0 to 0.10.0, but there has been 0.8.0 and 0.9.0 in between,
        #     i want all the changes, not just the ones from 0.9.0 to 0.10.0
        if len([v for v in all_versions if upgrade_from < v <= upgrade_to]) > 1:
            notes = get_release_notes_between_versions(
                release_notes, upgrade_from, upgrade_to
            )
        # else just get the single one.
        # this is because doing get_release_notes_between_versions would still return
        # the version <h2>, which would be stupid to show here
        else:
            notes = get_release_notes_for_version(release_notes, upgrade_to)
        print(
            f"""\
Release notes for v{upgrade_from} -> v{upgrade_to}
====================================

{render_markdown(notes).strip()}

---------------------------------------------
To see images, you can also read this online:
{url}
"""
        )
        return ask(q.Confirm("ans", message="Upgrade now?"))
    else:
        return answer == "Yes"


def upgrade(upgrade_from: Version, upgrade_to: Version):
    cmd = ["pip", "install", "--upgrade", f"ideaseed=={upgrade_to}"]
    if upgrade_from.major != upgrade_to.major:
        print(f"""\
You are upgrading to another major version (from {upgrade_from.major}.x.y to {upgrade_to.major}.x.y).
To prevent issues, the command you initially entered will not be run again automatically.

Please check for breaking changes that might affect the result of your command before running it again.""")
    else:
        print(f"Running {' '.join(cmd)}...")
        subprocess.run(cmd)
