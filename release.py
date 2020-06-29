#!/usr/bin/env python3
import os
from os import getenv
from os.path import abspath
from typing import *
from datetime import date
import sys
import re
import toml
import subprocess
import github
from dotenv import load_dotenv

load_dotenv(".env")

if (
    not getenv("GITHUB_TOKEN")
    or not getenv("PYPI_USERNAME")
    or not getenv("PYPI_PASSWORD")
):
    print(
        f"Specify GITHUB_TOKEN, PYPI_USERNAME and PYPI_PASSWORD in {abspath('./.env')}"
    )
    sys.exit(1)

# utility fns


def debug(txt: str = "", **kwargs):
    print(f"\033[32m{txt}\033[0m", **kwargs)


def shell(*cmd: str, dontrun: bool = False) -> Optional[str]:
    command = [str(arg) for arg in cmd]
    debug(f"$ " + " ".join(cmd))
    input("Press [ENTER] to continue...")
    if dontrun:
        return
    return subprocess.run(command, stdout=subprocess.PIPE).stdout.decode(
        encoding="utf8"
    )


# load toml files
with open("pyproject.toml", encoding="utf8") as file:
    pyproject = toml.load(file)

# set some variables
old = pyproject["tool"]["poetry"]["version"]
today = date.today().isoformat()
new = sys.argv[1]
pkgname = pyproject["tool"]["poetry"]["name"]
reponame: str = pyproject["tool"]["poetry"]["repository"].replace(
    "https://github.com/", ""
)
if reponame.endswith("/"):
    reponame = reponame[: len(reponame) - 1]  # Remove end slash

print(
    f"""\
Releasing a new version!!!1

Old version    : {old}
New version    : {new}
Today is       : {today}
Package name   : {pkgname}
Repository name: {reponame}
"""
)

if old == new:
    print(f"Version {new} has already been released.")

print(f"Updating version: {old} --> {new}")

# stash unstaged changes

shell(
    "git",
    "stash",
    "save",
    "--include-untracked",
    "--all",
    f'"Stash before release ({today})"',
)

# bump version

# Get the unreleased changes

with open("CHANGELOG.md", "r", encoding="utf8") as changelog:
    changelog_lines = changelog.read().split("\n")
    in_unreleased_section = False
    unreleased_section = ""
    in_preface = True
    preface = ""
    in_previous_versions = False
    previous_versions = ""
    in_links = False
    links = ""
    for line in changelog_lines:
        if line == "## [Unreleased]":
            in_preface = False
            in_unreleased_section = True
            continue
        if line.startswith(f"## [{old}]"):
            in_unreleased_section = False
            in_previous_versions = True
        if line.startswith(f"[Unreleased]: https://github.com/{reponame}/compare/"):
            in_previous_versions = False
            in_links = True
            continue

        if in_preface:
            preface += line + "\n"
        elif in_unreleased_section:
            unreleased_section += line + "\n"
        elif in_previous_versions:
            previous_versions += line + "\n"
        elif in_links:
            links += line + "\n"

    if not unreleased_section.strip():
        print("Aborting: No release notes")
        sys.exit()
    print("Got unreleased changes to put in next release:")
    print(unreleased_section.strip())
    print("----------------------------------------------")
    if input("Confirm? [y/N] ") != "y":
        print("Aborting.")
        sys.exit()

    # update CHANGELOG.md
    #     move what was in [Unreleased] in [$(VERSION)]

    previous_versions = (
        f"""## [{new}] - {today}
{unreleased_section}"""
        + previous_versions
    )

    links = (
        f"[Unreleased]: https://github.com/{reponame}/compare/v{new}...HEAD\n"
        + f"[{new}]: https://github.com/{reponame}/compare/v{old}...v{new}\n"
        + links
    )

    release_notes = unreleased_section

    unreleased_section = "## [Unreleased]\n"

    new_changelog = (
        "\n".join((preface, unreleased_section, previous_versions, links)).strip()
        + "\n"
    )
    debug(f"Wiriting new changelog {new_changelog!r}")

with open("CHANGELOG.md", "w", encoding="utf8") as changelog:
    changelog.write(new_changelog)

# bump version

with open(f"{pkgname}/constants.py", encoding="utf8") as constants_py:
    patt = re.compile(r'^VERSION = Version\(".+"\)$')
    lines = constants_py.read().split("\n")
    new_lines = lines
    for i, line in enumerate(lines):
        debug(f"Trying to match line {line!r}", end="")
        if patt.match(line):
            new_lines[i] = f'VERSION = Version("{new}")'
            debug("  Matched!")
            break
        else:
            debug()
    else:
        print(f"ERROR: version not replaced in {pkgname}/constants.py")
        sys.exit()

shell(
    "sed",
    "-i",
    "-e",
    f's/^VERSION = .*/VERSION = Version(\\"{new}\\")/g',
    f"{pkgname}/constants.py",
)

shell("poetry", "version", new)

# add all changes

shell("git", "add", ".")

# commit "🔖 Release $(VERSION)"

commit_msg = f"🔖 Release {new}"
shell("git", "commit", "-m", commit_msg)

# add tag v$(VERSION) to commit

latest_commit_hash = shell("git", "log", "--format=%H", "-n", "1").replace("\n", "")
debug(f"Got latest commit hash {latest_commit_hash!r}")

shell("git", "tag", "-a", f"v{new}", latest_commit_hash, "-m", commit_msg)

# push

shell("git", "push")

# push tag

shell("git", "push", "origin", f"v{new}")

# build

shell("poetry", "build")

# publish

shell(
    "poetry",
    "publish",
    "--username",
    getenv("PYPI_USERNAME"),
    "--password",
    getenv("PYPI_PASSWORD"),
)

# create github release

gh = github.Github(os.getenv("GITHUB_TOKEN"))
repo = gh.get_repo(reponame)
release = repo.create_git_release(tag=f"v{new}", name=new, message=release_notes)

release.upload_asset(
    f"dist/{pkgname}-{new}-py3-none-any.whl", label=f"Python wheel for {new}"
)
release.upload_asset(f"dist/{pkgname}-{new}.tar.gz", label=f"Source tarball for {new}")

milestones = repo.get_milestones()
for milestone in milestones:
    debug(
        f"Trying to match titles with milestone {milestone.title}: {milestone.title == new}"
    )
    if milestone.title == new:
        milestone.edit(state="closed", title=new)
        break
else:
    print(f"warn: No milestone with title {new!r} to close.")

shell("git", "stash", "pop")

with open(".env", "w", encoding="utf8") as file:
    print("Saving credentials to .env that probably got deleted:")
    file.write(
        f"""\
GITHUB_TOKEN="{getenv('GITHUB_TOKEN')}"
PYPI_USERNAME="{getenv('PYPI_USERNAME')}"
PYPI_PASSWORD="{getenv('PYPI_PASSWORD')}"
"""
    )
