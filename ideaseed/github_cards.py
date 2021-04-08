from __future__ import annotations

import re
import webbrowser
from collections import namedtuple
from pathlib import Path
from typing import Any, Callable, Optional, Tuple, TypeVar, Union, Iterable

import github.GithubObject
import inquirer as q
from github import Github
from github.GithubException import BadCredentialsException, TwoFactorException
from github.Issue import Issue
from github.Label import Label
from github.Milestone import Milestone
from github.NamedUser import NamedUser
from github.Project import Project
from github.ProjectColumn import ProjectColumn
from github.Repository import Repository
from rich import print

from ideaseed import ui
from ideaseed.authentication import Cache as BaseCache
from ideaseed.constants import UsageError
from ideaseed.utils import (answered_yes_to, ask_text,
                            error_message_no_object_found,
                            get_random_color_hexstring)


def validate_label_color(color: str):
    """
    Throws a `inquirer.errors.ValidationError` when the format isn't matched.
    (format: 6-digit hex int representing a color)
    """
    if not re.match(r"[a-fA-F0-9]{6}", color):
        raise q.errors.ValidationError(
            "", reason="Please use a valid color (6-digit hexadecimal integer)"
        )


class AuthCache(BaseCache):
    def __init__(self, path: Path):
        super().__init__(path=path, service="github")

    def login_from_cache(self) -> Optional[Github]:
        """
        Tries to login using the cached credentials.
        `None` is returned if the cache does not exist or is invalid.
        """
        try:
            return Github(
                login_or_token=self.cache["pat"] or self.cache["username"],
                password=self.cache["password"],
            )
        except Exception as error:
            print(f"[black on red]{error}")
            self.clear()

    def login_manually(self, method: str = None) -> Tuple[Github, dict[str, Any]]:

        LOGIN_METHODS = namedtuple("LoginMethods", ["PAT", "username"])(
            PAT="Personal Access Token", username="Username and password",
        )

        questions = [
            q.List(
                name="method",
                message="Log in using",
                choices=[LOGIN_METHODS.PAT, LOGIN_METHODS.username],
                ignore=lambda _: method is not None,
            ),
            q.Password(
                name="pat",
                message="Personal access token",
                ignore=lambda ans: (method or ans["method"]) != LOGIN_METHODS.PAT,
            ),
            q.Text(
                name="username",
                message="Username",
                ignore=lambda ans: (method or ans["method"]) != LOGIN_METHODS.username,
            ),
            q.Password(
                name="password",
                message="Password",
                ignore=lambda ans: (method or ans["method"]) != LOGIN_METHODS.username,
            ),
        ]
        answers = q.prompt(questions)

        method = answers["method"] or method

        if method == LOGIN_METHODS.PAT:
            try:
                gh = Github(answers["pat"])
                print(answers)
                return gh, answers
            except BadCredentialsException:
                print("Bad token")
                return self.login_manually(method=method)
        else:
            try:
                gh = Github(answers["username"], answers["password"])
                print(answers)
                return gh, answers
            except TwoFactorException:
                print(
                    "Your account uses two-factor authentification. Please use a personal access token instead."
                )
                return self.login_manually(method=LOGIN_METHODS.username)
            except BadCredentialsException:
                print("Bad credentials")
                return self.login_manually(method=method)


def resolve_self_repository_shorthand(gh: Github, repo: str) -> str:
    """
    Adds USERNAME/ to a `repo` that has no slashes
    """
    if "/" not in repo:
        return gh.get_user().login + "/" + repo
    return repo


def resolve_defaults(
    column: Optional[str],
    project: Optional[str],
    default_project: str,
    default_column: str,
    repo_full_name: str,
    username: str,
) -> tuple[str, str]:
    """
    Resolves defaults for `COLUMN` and `PROJECT` using `--default-*` arguments
    ``repo_full_name`` must be of the form ``OWNER/REPO``

    Returns a `(project, column)` tuple.
    
    >>> resolve_default_arguments(
    ...     column=None, 
    ...     project='testy',
    ...     default_project='1', 
    ...     default_column='{project}',
    ...     repo_full_name='ewen-lbh/project',
    ...     username='ewen-lbh',
    ... )
    "testy", "testy"
    """
    owner, repository = repo_full_name.split("/")
    if not project and not default_project:
        return None, None
    project = project or default_project.format(
        owner=owner, repository=repository, username=username
    )
    if not column and not default_column:
        return project, None
    column = column or default_column.format(
        owner=owner, repository=repository, username=username, project=project
    )

    return project, column


def interactively_create_label(repo: Repository, name: str):
    label_data = q.prompt(
        [
            # TODO: Proper color prompt with color names, live color preview, default value that is removed once you start typing.
            #       will need to use prompt-toolkit at some point.
            # q.Text(
            #     "color",
            #     message="Choose a color for your label",
            #     validate=validate_label_color,
            #     default=lambda ans: f"{randint(0x0, 0xFFFFFF):6x}".upper()
            # ),
            q.Text(
                "description", message="A short description of your label", default="",
            ),
        ]
    )

    color = get_random_color_hexstring()
    print(f"Creating label {ui.Label(name, color)}...")
    repo.create_label(name=name, color=color, **label_data)


def tag_names_to_labels(
    repo: Repository, create_missing: bool, tag: list[str]
) -> list[Label]:
    if not tag:
        return []
    all_labels = repo.get_labels()
    labels: list[Label] = []
    for label_name in tag:
        label = search_for_object(
            all_labels,
            label_name,
            create_missing=create_missing,
            object_name="label",
            create=lambda: interactively_create_label(repo, label_name),
        )
        if label:
            labels.append(label)
    return labels


def get_milestone_from_name(
    repo: Repository, create_missing: bool, name: str
) -> Milestone:
    return search_for_object(
        repo.get_milestones(),
        name,
        create_missing=create_missing,
        object_name="milestone",
        create=lambda: repo.create_milestone(title=name),
        get_name=lambda obj: obj.title,
    )


def create_and_show_issue(
    dry_run: bool,
    body: str,
    repo: Repository,
    title: str,
    milestone: Optional[Milestone],
    project: Optional[Project],
    labels: list[Label],
    column: Optional[ProjectColumn],
    assignees: list[NamedUser],
):
    issue = None
    if not dry_run:
        issue = repo.create_issue(
            title=title or body,
            body=body if title else "",
            assignees=assignees,
            labels=labels,
            milestone=(milestone or github.GithubObject.NotSet),
        )
        if column is not None:
            column.create_card(content_id=issue.id, content_type="Issue")
        url = issue.html_url
    else:
        url = None

    ui.show(
        title=title,
        right_of_title=with_link(issue),
        description=body,
        labels=map(lambda l: to_ui_label(l, repo), labels),
        card_title=get_card_title(repo),
        milestone=with_link(milestone) if milestone else None,
        assignees=map(linkify_github_username, assignees),
        project=with_link(project) if project else None,
        project_column=ui.href(column.name, project.html_url) if column else None,
        url=url,
    )


def get_card_title(repo_or_user: Union[Repository, NamedUser]) -> str:
    if isinstance(repo_or_user, Repository):
        return f"{with_link(repo_or_user.owner)}/{with_link(repo_or_user)}"
    elif isinstance(repo_or_user, NamedUser):
        return f"@{with_link(repo_or_user)}"
    else:
        raise TypeError("repo_or_user should be of type NamedUser or Repository")


def create_and_show_github_card(
    dry_run: bool,
    column: ProjectColumn,
    project: Project,
    repo_or_user: Union[Repository, NamedUser],
    title: str,
    body: str,
):
    if not dry_run:
        column.create_card(note=body)
        url = project.html_url
    else:
        url = None

    ui.show(
        title=title,
        right_of_title="",
        description=body,
        labels=[],
        card_title=get_card_title(repo_or_user),
        milestone=None,
        assignees=None,
        project=with_link(project),
        project_column=ui.href(column.name, project.html_url),
        url=url,
    )


class AbstractCard:
    """ Represents a future github card/issue, with all attributes refering to their names instead of their resolved github objects """
    


def push_to_repo(
    auth_cache: Optional[str],
    body: str,
    title: Optional[str],
    repo: str,
    project: Optional[str],
    column: Optional[str],
    assign: list[str],
    self_assign: bool,
    milestone: Optional[str],
    tag: list[str],
    default_project: Optional[str],
    default_column: Optional[str],
    create_missing: bool,
    no_issue: bool,
    dry_run: bool,
    open: bool,
    **_,
) -> None:
    if auth_cache is None:
        raise NotImplementedError(
            "You need to specify a cache for now, I'll get to the --keyring implementation later"
        )
    gh = AuthCache(Path(auth_cache)).login()
    repo_full_name = resolve_self_repository_shorthand(gh, repo)
    repo: Repository = gh.get_repo(repo_full_name)
    username = gh.get_user().login
    assignees = assign or ([username] if self_assign else [])
    project, column = resolve_defaults(
        column, project, default_project, default_column, repo_full_name, username
    )
    # user specified a name
    if project and column:
        project, column = get_project_and_column(repo, project, column, create_missing)
        # but it was not found nor created
        if not (project and column):
            return
    # user _did not_ specify a name (ie do not create a project card)
    else:
        project, column = None, None

    project: Optional[Project]
    column: Optional[ProjectColumn]

    # Get all labels
    labels = tag_names_to_labels(repo, create_missing, tag)

    # Some labels where not found
    if len(labels) != len(tag):
        return

    if milestone is not None:
        milestone = get_milestone_from_name(repo, create_missing, milestone)

    url = None if dry_run else repo.html_url

    if not no_issue:
        create_and_show_issue(
            dry_run=dry_run,
            body=body,
            title=title,
            repo=repo,
            milestone=milestone,
            project=project,
            labels=labels,
            column=column,
            assignees=assignees,
        )

    elif project and column:
        create_and_show_github_card(
            dry_run=dry_run,
            body=body,
            column=column,
            project=project,
            repo=repo,
            title=title,
        )
    else:
        UsageError(
            "Cannot use --no-issue without a project and column (the idea needs to be put somewhere!)"
        )

    # Open project URL
    if open and url:
        webbrowser.open(url)


def push_to_user(
    body: str,
    title: Optional[str],
    project: Optional[str],
    column: Optional[str],
    create_missing: bool,
    auth_cache: Optional[str],
    dry_run: bool,
    open: bool,
    **_,
) -> None:
    if title:
        body = f"# {title}\n\n{body}"

    gh = AuthCache(auth_cache).login()
    user = gh.get_user()
    username = user.login
    project, column = get_project_and_column(
        # XXX: for some reason, we have to call get_user again to get a NamedUser
        # and not an AuthenticatedUser, because those don't have .get_projects() defined
        gh.get_user(user.login),
        project,
        column,
        create_missing,
    )

    if not column or not project:
        return

    url = None if dry_run else project.html_url

    create_and_show_github_card(
        dry_run=dry_run,
        column=column,
        project=project,
        repo=user,
        title=title,
        body=body,
    )

    # Open project URL
    if open and url:
        webbrowser.open(url)


T = TypeVar("T")


def search_for_object(
    objects: Iterable[T],
    name: str,
    create_missing: bool,
    object_name: str,
    create: Callable[[], Optional[T]],
    get_name: Callable[[T], str] = lambda obj: obj.name,
) -> Optional[T]:
    the_object = None
    for obj in objects:
        if get_name(obj).lower() == name.lower():
            the_object = obj
            break
    else:
        if create_missing and answered_yes_to(
            f"Create missing {object_name} {name!r}?"
        ):
            the_object = create()
        else:
            return

    # Not found and not created
    if the_object is None:
        print(error_message_no_object_found(objtype=object_name, objname=name))
        return

    return the_object


def get_project_and_column(
    repo: Repository, project_name: str, column_name: str, create_missing: bool
) -> tuple[Optional[Project], Optional[ProjectColumn]]:
    """
    Gets a project and column from a repo
    """
    project = search_for_object(
        repo.get_projects(),
        project_name,
        create_missing=create_missing,
        object_name="project",
        create=lambda: repo.create_project(
            name=project_name, body=ask_text("Enter the project's description..."),
        ),
    )

    if project is None:
        return None, None

    column = search_for_object(
        project.get_columns(),
        column_name,
        create_missing=create_missing,
        object_name="column",
        create=lambda: project.create_column(
            name=column_name, body=ask_text("Enter the column's description..."),
        ),
    )

    return project, column


def to_ui_label(label: Label, repo: Repository) -> ui.Label:
    return ui.Label(
        name=label.name,
        color=label.color,
        url=f"{repo.html_url}/issues/?q=is:issue+is:open+label:{label.name}",
    )


def with_link(o: Union[ProjectColumn, Project, Issue, NamedUser, Milestone]) -> str:
    """
    Returns `o.name` (or `o.title`, or `o.login`) wrapped around a terminal link sequence pointing to `o.html_url` (or `o.url`)
    Special case: uses `f"#{o.number}"` as a name for issues
    """
    # can't wait for py310 pattern matching
    if not o:
        return ""
    name = (
        f"#{o.number}"
        if isinstance(o, Issue)
        else o.login
        if isinstance(o, NamedUser)
        else o.title
        if isinstance(o, Milestone)
        else o.name
    )
    if name is None:
        raise ValueError(
            f"ideaseed.github_cards.with_link: object {o!r} has neither .number, nor .name, nor .title, nor .login attributes"
        )
    return ui.href(name, o.url if isinstance(o, ProjectColumn) else o.html_url)


def linkify_github_username(username: str) -> str:
    # XXX: Assuming that github will not change its username URL scheme. Highly probable.
    return ui.href(username, f"https://github.com/{username}")


if __name__ == "__main__":
    import doctest

    doctest.testmod()
