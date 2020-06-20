#!/usr/bin/env python3
import os
from sys import version
from typing import *
from datetime import date
import sys
import re
import toml
import subprocess
import github

# utility fns


def debug(txt: str = "", **kwargs):
    print(f"\033[32m{txt}\033[0m", **kwargs)


def shell(*cmd: str, dontrun: bool = False) -> str:
    cmd = [str(arg) for arg in cmd]
    debug(f"$ " + " ".join(cmd))
    input("Press [ENTER] to continue...")
    if dontrun:
        return
    return subprocess.run(
        " ".join(cmd), shell=True, stdout=subprocess.PIPE
    ).stdout.decode(encoding="utf8")


def shell(*cmd: str):
    return shell(*cmd, dontrun=True)


# load toml files
with open("pyproject.toml", encoding="utf8") as file:
    pyproject = toml.load(file)

# set some variables
old = pyproject["tool"]["poetry"]["version"]
today = date.today().isoformat()
new = sys.argv[1]

print(f"Updating version: {old} --> {new}")

# stash unstaged changes

# shell('git', 'stash', '--include-untracked','--all', '-m "Stash before release"')

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
        if line.startswith(
            "[Unreleased]: https://github.com/ewen-lbh/ideaseed/compare/"
        ):
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

    print("Got unreleased changes to put in next release:")
    print(unreleased_section)
    print("----------------------------------------------")
    if input("Confirm? [y/N]") != "y":
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
        f"[Unreleased]: https://github.com/ewen-lbh/ideaseed/compare/v{new}...HEAD\n"
        + f"[{new}]: https://github.com/ewen-lbh/ideaseed/compare/v{old}...v{new}\n"
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

with open("ideaseed/constants.py", encoding="utf8") as constants_py:
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
        print("ERROR: version not replaced in ideaseed/constants.py")
        sys.exit()

shell("poetry", "version", new)

# add all changes

shell("git", "add", ".")

# commit "🔖 Release $(VERSION)"

commit_msg = f"'🔖 Release {new}'"
shell("git", "commit", "-m", commit_msg)

# add tag v$(VERSION) to commit

latest_commit_hash = shell("git", "log", "--format=%H", "-n", "1").replace("\n", "")
debug(f"Got latest commit hash {latest_commit_hash!r}")

shell("git", "tag", f"-a=v{new}", latest_commit_hash, "-m", commit_msg)

# push

shell("git", "push")

# push tag

shell("git", "push", "origin", f"v{new}")

# build

shell("poetry build")

# publish

shell("poetry publish")

# create github release

gh = github.Github(input("gh tok > "))
release = gh.get_repo("ewen-lbh/ideaseed").create_git_release(
    tag=f"v{new}", name=new, message=release_notes
)

release.upload_asset(
    f"dist/ideaseed-{new}-py3-none-any.whl", label=f"Python wheel for {new}"
)
release.upload_asset(f"dist/ideaseed-{new}.tar.gz", label=f"Source tarball for {new}")

#     attach files dist/ideaseed-$(VERSION)*
#     set title as $(VERSION)
#     set tag as v$(VERSION)
#     set description to CHANGELOG.md's $(VERSION) - $(DATE)'s section
# pop stashed changes

shell("git", "stash", "pop")
