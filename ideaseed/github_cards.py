from __future__ import annotations

import re
import webbrowser
from collections import namedtuple
from pathlib import Path
from typing import Any, Callable, Iterable, Optional, Tuple, TypeVar, Union

import github.GithubObject
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
from ideaseed.utils import (answered_yes_to, ask,
                            error_message_no_object_found,
                            get_random_color_hexstring)


def validate_label_color(color: str):
    """
    Throws a `inquirer.errors.ValidationError` when the format isn't matched.
    (format: 6-digit hex int representing a color)
    """
    return re.match(r"[a-fA-F0-9]{6}", color)


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
                password=self.cache["password"] if "password" in self.cache else None,
            )
        except Exception as error:
            print(f"[black on red]{error}")
            self.clear()

    def login_manually(self, method: str = None) -> Tuple[Github, dict[str, Any]]:
        LOGIN_METHODS = namedtuple("LoginMethods", ["PAT", "username"])(
            PAT="Personal Access Token", username="Username and password",
        )

        method = method or ask(
            "Log in using",
            choices={"0": LOGIN_METHODS.PAT, "1": LOGIN_METHODS.username},
        )

        if method == LOGIN_METHODS.PAT:
            pat = ask("Personal access token", password=True)
            try:
                gh = Github(pat)
                # just instanciating does not mean auth succeeded
                # seems like you need to _really_ hit Auth-retricted APIs,
                # even gh.get_user() does not work.
                # There does not seem to be a method made for auth-checking,
                # so I'm using that. sigh...
                gh.get_user().get_user_issues().get_page(0)
                return gh, dict(method=method, pat=pat)
            except BadCredentialsException:
                print("Bad token")
                return self.login_manually(method=method)
            except Exception as e:
                print(repr(e))
                return self.login_manually(method=method)
        else:
            username = ask("Username")
            password = ask("Password", password=True)
            try:
                gh = Github(username, password)
                gh.get_user().get_user_issues().get_page(0)
                return gh, dict(method=method, username=username, password=password)
            except TwoFactorException:
                print(
                    "Your account uses two-factor authentification. Please use a personal access token instead."
                )
                return self.login_manually(method=LOGIN_METHODS.username)
            except BadCredentialsException:
                print("Bad credentials")
                return self.login_manually(method=method)
            except Exception as e:
                print(repr(e))
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
    
    >>> resolve_defaults(
    ...     column=None, 
    ...     project='testy',
    ...     default_project='1', 
    ...     default_column='{project}',
    ...     repo_full_name='ewen-lbh/project',
    ...     username='ewen-lbh',
    ... )
    ('testy', 'testy')
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
    label_data = {
        "color": get_random_color_hexstring(),
        "description": ask("A short description of your label"),
        "name": name,
    }
    print(f"Creating label {ui.Label(name, label_data['color'])}...")
    return repo.create_label(**label_data)


def label_names_to_labels(
    repo: Repository, create_missing: bool, label: list[str]
) -> list[Label]:
    label_names = label.copy()  # list of `str`s, no need to deepcopy.
    if not label_names:
        return []
    all_labels = repo.get_labels()
    labels: list[Label] = []
    for label_name in label_names:
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
        assignees=list(
            map(linkify_github_username, assignees)
        ),  # maps are generators, and generators exhaust!
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
        assignees=[],
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
    label: list[str],
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
    assignees = assign
    if self_assign and not len(assignees):
        assignees = [username]
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
    labels = label_names_to_labels(repo, create_missing, label)

    # Some labels where not found
    if len(labels) != len(label):
        return

    if milestone is not None:
        milestone: Milestone = get_milestone_from_name(repo, create_missing, milestone)
        if milestone.state != "closed":
            if not answered_yes_to(
                f"[yellow]:warning:[/] The selected milestone is {milestone.state}. Use this milestone?"
            ):
                return

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
    default_project: str,
    default_column: str,
    **_,
) -> None:
    # FIXME: creates a duplicated title in the card.
    #           the thing is that the card displays the title and the body
    #           but github cards themselves do not have a title, so we need
    #           to include the title in the body as an <h1>
    #           but the same body gets passed to `ui.show`, so it appears twice:
    #           as the `title`, and as the <h1> of `body`.
    if title:
        body = f"# {title}\n\n{body}"

    gh = AuthCache(Path(auth_cache)).login()
    # XXX: for some reason, we have to call get_user again to get a NamedUser
    # and not an AuthenticatedUser, because those don't have .get_projects() defined
    user = gh.get_user(gh.get_user().login)
    project, column = resolve_defaults(
        column,
        project,
        default_project=default_project,
        default_column=default_column,
        repo_full_name=f"{user.login}/",
        username=user.login,
    )
    project, column = get_project_and_column(user, project, column, create_missing,)

    if not column or not project:
        return

    url = None if dry_run else project.html_url

    create_and_show_github_card(
        repo_or_user=user,
        dry_run=dry_run,
        column=column,
        project=project,
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
            f"Create missing {object_name} {name!r}?", True
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
            name=project_name, body=ask("Enter the project's description..."),
        ),
    )

    if project is None:
        return None, None

    column = search_for_object(
        project.get_columns(),
        column_name,
        create_missing=create_missing,
        object_name="column",
        create=lambda: project.create_column(name=column_name),
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

    if isinstance(o, ProjectColumn) or isinstance(o, Milestone):
        url = o.url
    else:
        url = o.html_url

    return ui.href(name, url)


def linkify_github_username(username: str) -> str:
    # XXX: Assuming that github will not change its username URL scheme. Highly probable.
    return ui.href(username, f"https://github.com/{username}")


if __name__ == "__main__":
    import doctest

    doctest.testmod()
