from __future__ import annotations

from typing import Any, Optional, Union

from semantic_version import Version

VERSION = Version("1.0.0")

RELEASES_RSS_URL = "https://pypi.org/rss/project/ideaseed/releases.xml"

COLOR_NAME_TO_HEX_MAP: dict[str, str] = {
    "Blue": "AECBFA",
    "Brown": "E6C9A8",
    "DarkBlue": "AECBFA",
    "Gray": "E8EAED",
    "Green": "CCFF90",
    "Orange": "FBBC04",
    "Pink": "FDCFE8",
    "Purple": "D7AEFB",
    "Red": "F28B82",
    "Teal": "A7FFEB",
    "White": "FFFFFF",
    "Yellow": "FFF475",
}

COLOR_ALIASES = {
    "Cyan": "Teal",
    "Indigo": "DarkBlue",
    "Grey": "Gray",
    "Magenta": "Purple",
}

VALID_COLOR_NAMES = list(COLOR_ALIASES.keys()) + list(COLOR_NAME_TO_HEX_MAP.keys())


class UsageError(Exception):
    pass
