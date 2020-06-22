from ideaseed.constants import COLOR_NAME_TO_HEX_MAP, C_PRIMARY
from typing import *

from github.Repository import Repository
from ideaseed.utils import dye, english_join
from wcwidth import wcswidth
import textwrap
import cli_box
from strip_ansi import strip_ansi

ABOUT_SCREEN = """


                ██████████  ██  ██
                ██      ██  ██  ██
                ██████████  ██  ██
                ██      ██  ██  ██
                ██████████████████
                ██      ██      ██
                ██████████      ██
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

{issue_card}{timeline_item_milestone}{timeline_item_assignees}
 │
[◫] @{username} added this to {column} in {project}
 │
 →  Issue available at {url}
"""

GITHUB_ISSUE_TIMELINE_ITEM_MILESTONE_ART = """
 │
[⚐] @{username} added this to the {title} milestone"""

GITHUB_ISSUE_TIMELINE_ITEM_ASSIGNEES_ART = """
 │
[Ω] @{username} {assignation_sentence}"""

GITHUB_CARD_ART = """\
{card_header}
{content}
"""

GITHUB_ART = """\
{card}
 │
 →  Project card available at {url}
"""

def strwidth(o: str) -> int:
    """
    Smartly calculates the actual width taken on a terminal of `o`. 
    Handles ANSI codes (using `strip-ansi`) and Unicode (using `wcwidth`)
    """
    return wcswidth(strip_ansi(o))

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
    left_max_len = CARD_INNER_WIDTH - strwidth(right) - 2
    if strwidth(left) >= left_max_len:
        left = f"{left:.{left_max_len-1}}" + "…"

    spaces = " " * (CARD_INNER_WIDTH - strwidth(left) + 2 - strwidth(right))

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
    title: Optional[str],
    pinned: bool,
    tags: List[str],
    url: str,
    body: str,
    color: str,
) -> str:
    card_header = make_card_header(
        left=dye(title or "", style="bold"), right=GOOGLE_KEEP_PINNED if pinned else ""
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
        [dye(line, fg=COLOR_NAME_TO_HEX_MAP.get(color)) for line in card.split("\n")]
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
            content=wrap_card_content(body), card_header=dye(card_header, style="dim")
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
    milestone: Optional[str],
) -> str:
    card_header = make_card_header(
        left=dye(title or "", style="bold"), right=dye(f"#{issue_number}", fg=C_PRIMARY)
    )
    timeline_item_milestone = ""
    if milestone:
        timeline_item_milestone = GITHUB_ISSUE_TIMELINE_ITEM_MILESTONE_ART.format(
            username=username, title=dye(milestone, style="bold")
        )
    timeline_item_assignees = ""
    if assignees:
        timeline_item_assignees = GITHUB_ISSUE_TIMELINE_ITEM_ASSIGNEES_ART.format(
            username=username,
            assignation_sentence=(
                "self-assigned this"
                if assignees == [username]
                else (
                    "assigned "
                    + english_join([dye("@" + a, style="bold") for a in assignees])
                    + " to this"
                )
            ),
        )
    card = cli_box.rounded(
        ISSUE_CARD_ART.format(
            card_header=card_header,
            content=wrap_card_content(body),
            labels=" ".join([TAGS_ART.format(tag=t) for t in labels]),
        ),
        align="left",
    )

    return ISSUE_ART.format(
        owner=dye(owner, fg=C_PRIMARY, style="bold"),
        repository=dye(repository, fg=C_PRIMARY, style="bold"),
        project=dye(project, fg=C_PRIMARY, style="bold"),
        column=dye(column, fg=C_PRIMARY, style="bold"),
        username=username,
        url=dye(url, style="bold"),
        issue_card=card,
        timeline_item_milestone=timeline_item_milestone,
        timeline_item_assignees=timeline_item_assignees,
    )

