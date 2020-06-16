from typing import Optional
from typing import *
import colr


def dye(
    text: str,
    fg: Optional[int] = None,
    bg: Optional[int] = None,
    style: Optional[str] = None,
    no_closing: bool = False,
):
    return colr.color(
        text=text,
        fore=f"{fg:x}" if fg is not None else None,
        back=f"{bg:x}" if bg is not None else None,
        style=style,
        no_closing=no_closing,
    )
