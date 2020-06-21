from ideaseed.constants import COLOR_NAME_TO_HEX_MAP, C_PRIMARY
from typing import *

from github.Repository import Repository
from ideaseed.utils import dye, english_join
from wcwidth import wcswidth
import textwrap
import cli_box

ABOUT_SCREEN = """


                ██████████  ██  ██  
                ██      ██  ██  ██  
                ██████████  ██  ██ 
                ██      ██  ██  ██ 
                ██████████████████  <- that's my personal logo,
                ██      ██      ██     i didn't make one for 
                ██████████      ██     ideaseed, yet™
                ██      ██      ██ 
                ██████████      ██ 
      
            ideaseed v{version}
            by Ewen Le Bihan
            more at https://ewen.works
      
                ~ thx to these ppl ~

https://github.com/kiwiz
    This madman reverse-engineered Google Keep's
    internal REST API so that anyone could 
    use it with ease.
                    
https://github.com/PyGithub
    This one of the cleanest libs I've ever used.
    Like `requests`-level cleanliness.
                    
https://github.com/docopt
    Designing CLIs with this is a fucking breeze.
    I can almost copy-paste documentation into
    a docstring and call it a day, it's crazy.
"""

CARD_INNER_WIDTH = 50
CARD_LINE_SEPARATOR = "─" * CARD_INNER_WIDTH

ISSUE_ART = """\
Opening issue in {owner} › {repository} › {project} › {column}...

{issue_card}
 │
[Ω] @{username} {assignation_sentence}
 │
[◫] @{username} added this to {column} in {project}
 │
 →  Issue available at {url}
"""

GITHUB_CARD_ART = """\
{card_header}
{content}
"""

GITHUB_ART = """\
{card}
 │
 →  Project card available at {url}
"""


def make_card_header(left: str, right: str) -> str:
    """
    Returns
    "{left}{enough spaces}{right}"
    
    Truncates `left` to leave enough spaces.
    spacing is at a minimum of two columns.
    """
    left = str(left)
    right = str(right)
    # Card width
    # Calculate max length of title
    left_max_len = CARD_INNER_WIDTH - wcswidth(right) - 2
    if wcswidth(left) >= left_max_len:
        left = f"{left:.{left_max_len-1}}" + "…"

    spaces = " " * (CARD_INNER_WIDTH - wcswidth(left) + 2 - wcswidth(right))

    return left + spaces + right


ISSUE_CARD_ART = f"""\
{{card_header}}
{{content}}
{CARD_LINE_SEPARATOR}
{{labels}}
"""

TAGS_ART = "[{tag}]"

GOOGLE_KEEP_ART = """\
Adding card to your Google Keep account:

{card}
 │
 →  Available at {url}
"""

GOOGLE_KEEP_CARD_ART = f"""\
{{card_header}}
{{content}}
{CARD_LINE_SEPARATOR}
{{tags}}
"""

GOOGLE_KEEP_PINNED = "⚲ Pinned"


def make_google_keep_art(
    title: Optional[str], pinned: bool, tags: List[str], url: str, body: str, color: str
) -> str:
    card_header = make_card_header(
        left=title or "", right=GOOGLE_KEEP_PINNED if pinned else ""
    )
    card = cli_box.rounded(
        GOOGLE_KEEP_CARD_ART.format(
            card_header=card_header,
            content=body,
            tags=" ".join([TAGS_ART.format(tag=t) for t in tags])
            if tags
            else "No tags.",
        ),
        align="left",
    )

    card = "\n".join(
        [
            dye(line, bg=COLOR_NAME_TO_HEX_MAP[color], fg=0x000)
            for line in card.split("\n")
        ]
    )
    return GOOGLE_KEEP_ART.format(card=card, url=url)


def wrap_card_content(body: str) -> str:
    return textwrap.fill(body, width=CARD_INNER_WIDTH, replace_whitespace=False)


def make_github_project_art(
    owner: str, repository: str, project: str, column: str, body: str, url: str
):
    card_header = make_card_header(
        left=f"{owner}/{repository}", right=f"{column} in {project}"
    )
    card = cli_box.rounded(
        GITHUB_CARD_ART.format(
            content=wrap_card_content(body), card_header=card_header
        ),
        align="left",
    )
    return GITHUB_ART.format(card=card, url=url)


def make_github_user_project_art(
    username: str, project: str, column: str, body: str, url: str
):
    card_header = make_card_header(left=f"@{username}", right=f"{column} in {project}")
    card = cli_box.rounded(
        GITHUB_CARD_ART.format(
            content=wrap_card_content(body), card_header=card_header
        ),
        align="left",
    )
    return GITHUB_ART.format(card=card, url=url)


def make_github_issue_art(
    owner: str,
    repository: str,
    project: str,
    column: str,
    username: str,
    url: str,
    issue_number: int,
    labels: List[str],
    body: str,
    title: Optional[str],
    assignees: List[str],
) -> str:
    card_header = make_card_header(left=title or "", right=f"#{issue_number}")
    card = cli_box.rounded(
        ISSUE_CARD_ART.format(
            card_header=card_header,
            content=wrap_card_content(body),
            labels=" ".join([TAGS_ART.format(tag=t) for t in labels]),
        ),
        align="left",
    )
    assignation_sentence = (
        "self-assigned this"
        if assignees == [username]
        else (
            "assigned "
            + english_join([dye("@" + a, style="bold") for a in assignees])
            + " to this"
        )
    )
    return ISSUE_ART.format(
        owner=dye(owner, fg=C_PRIMARY, style="bold"),
        repository=dye(repository, fg=C_PRIMARY, style="bold"),
        project=dye(project, fg=C_PRIMARY, style="bold"),
        column=dye(column, fg=C_PRIMARY, style="bold"),
        username=dye(username, style="bold"),
        url=dye(url, style="bold"),
        issue_card=card,
        assignation_sentence=assignation_sentence,
    )
