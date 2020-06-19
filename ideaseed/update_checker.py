from typing import *
from ideaseed.constants import RELEASES_RSS_URL
from xml.dom.minidom import parseString as parse_xml
import cli_box
import requests
from ideaseed.utils import ask
from inquirer import Confirm
from semantic_version import Version
import subprocess


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


def notification(upgrade_from: Version, upgrade_to: Version) -> str:
    return cli_box.rounded(
        f"""==== Update available! ====

A new version of ideaseed is available for download:
{upgrade_from} -> {upgrade_to}
"""
    )


def prompt(upgrade_to: Version):
    return ask(Confirm("ans", message=f"Upgrade to v{upgrade_to} now?"))


def upgrade(upgrade_to: Version):
    cmd = ["pip", "install", "--upgrade", f"ideaseed=={upgrade_to}"]
    print(f"Running {' '.join(cmd)}...")
    subprocess.run(cmd)
