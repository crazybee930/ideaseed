"""
Takes care of saving a copy of ideas to disk (if enable with --local-copy=DIR)

Will save in {--local-copy}/{project name}/{slug of (title or body's first line)}
"""

from pathlib import Path
from typing import Optional

import yaml
from recordclass import RecordClass
from slugify import slugify

from ideaseed.utils import answered_yes_to


class Idea(RecordClass):
    assignees: list[str] = []
    body: str = ""
    color: str = ""
    column: str = ""
    labels: list[str] = []
    milestone: str = ""
    pinned: bool = False
    project: str = ""
    repo: str = ""
    title: str = ""
    url: str = ""

    @property
    def as_markdown(self) -> str:
        return f"""---
{yaml.dump(self._header_dict).strip()}
---

# {self.title}

{self.body}
"""

    @property
    def _header_dict(self) -> dict:
        """
        Returns a YAML header to be used by `self.as_markdown`

        >>>
        """
        excluded_keys = "body", "title", "repo"
        return {
            k: v
            for k, v in self._asdict().items()
            if v
            and k not in excluded_keys
            and (
                # also don't add color: White since it's the default
                not (k == "color" and v == "White")
            )
        }


def save(local_copy: Path, idea: Idea, repo: str, **_) -> str:
    """
    Saves a local copy of the given Idea to the right path
    Returns the path where the file was written.
    Returns "" if the file was not written at all.
    """

    filepath = get_path(
        root_dir=local_copy, repo_full=repo, title=idea.title, body=idea.body
    )
    if filepath.exists() and not answered_yes_to(
        f"The local copy [bold blue]{filepath.relative_to(local_copy)}[/] already exists. Overwrite it?"
    ):
        return ""

    filepath.parent.mkdir(parents=True, exist_ok=True)
    filepath.write_text(idea.as_markdown)
    return filepath


def first_line(text: str) -> str:
    return text.splitlines()[0]


def get_path(
    root_dir: Path, repo_full: Optional[str], title: Optional[str], body: str
) -> Path:
    repo_full = repo_full or ""
    if "/" in repo_full:
        user, repo = repo_full.split("/")
    else:
        user, repo = "", repo_full

    return root_dir / user / repo / (slugify(title or first_line(body)) + ".md")
