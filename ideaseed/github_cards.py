from __future__ import annotations

import json
from json.decoder import JSONDecodeError
import re
import webbrowser
from pathlib import Path
from typing import Callable, Optional, TypeVar
from github.Milestone import Milestone
from github.Repository import Repository

import inquirer as q
from github import Github
from github.GithubException import BadCredentialsException, TwoFactorException
from github.Label import Label
from github.Project import Project
from github.ProjectColumn import ProjectColumn
import github.GithubObject

from ideaseed.constants import C_PRIMARY
from ideaseed.dumb_utf8_art import (
    make_github_issue_art,
    make_github_project_art,
    make_github_user_project_art,
)
from ideaseed.utils import (
    answered_yes_to,
    ask_text,
    dye,
    error_message_no_object_found,
    get_random_color_hexstring,
    readable_text_color_on,
)


def validate_label_color(answers: dict, color: str):
    """
    Throws a `inquirer.errors.ValidationError` when the format isn't matched.
    (format: 6-digit hex int representing a color)
    """
    if not re.match(r"[a-fA-F0-9]{6}", color):
        raise q.errors.ValidationError(
            "", reason="Please use a valid color (6-digit hexadecimal integer)"
        )


def login_with_cache(cache_path: Path) -> Optional[Github]:
    """
    Tries to login using the cached credentials.
    `None` is returned if the cache does not exist or is invalid.
    """
    if cache_path.exists():
        try:
            creds = json.loads(cache_path.read_text(encoding="utf-8")).get("github")
        except JSONDecodeError:
            creds = None
        if not creds:
            return None
        creds = (
            [creds["username"], creds["password"]]
            if creds["pat"] is None
            else [creds["pat"]]
        )
        try:
            gh = Github(*creds)
            gh.get_user().name
            return gh
        except BadCredentialsException:
            return None
        except TwoFactorException:
            return None
    return None


def write_auth_cache(data, cache_path: Path):
    cache_path.parent.mkdir(exist_ok=True, parents=True)
    cache_path.touch()
    try:
        existing_data = json.loads(cache_path.read_text("utf-8"))
    except JSONDecodeError:
        existing_data = {}
    cache_path.write_text(json.dumps(existing_data | {"github": data}))


def login(auth_cache: str, method: Optional[str] = None, **_) -> Github:
    """
    Returns a `Github` instance to interact with.
    Prompts the user to login, either via username/password
    or using a Personal Access Token
    """
    gh = login_with_cache(Path(auth_cache))
    if gh is not None:
        return gh
    else:
        del gh

    questions = [
        q.List(
            name="method",
            message="Log in using",
            choices=["Personal Access Token", "Username and password"],
            ignore=lambda _: method is not None,
        ),
        q.Password(
            name="pat",
            message="Personal Access Token",
            ignore=lambda ans: (method or ans["method"]) != "Personal Access Token",
        ),
        q.Text(
            name="username",
            message="Username",
            ignore=lambda ans: (method or ans["method"]) != "Username and password",
        ),
        q.Password(
            name="password",
            message="Password",
            ignore=lambda ans: (method or ans["method"]) != "Username and password",
        ),
    ]
    answers = q.prompt(questions)

    if auth_cache and answers:
        write_auth_cache(answers, cache_path=Path(auth_cache))

    if answers["pat"] is not None:
        try:
            gh = Github(answers["pat"])
            return gh
        except BadCredentialsException:
            print("Bad token")
            return login(auth_cache, method)
    else:
        try:
            gh = Github(answers["username"], answers["password"])
            return gh
        except TwoFactorException:
            print(
                "Your account uses two-factor authentification. Please use a personal access token instead."
            )
            return login(auth_cache, method="Personal Access Token")
        except BadCredentialsException:
            print("Bad credentials")
            return login(auth_cache, method)


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
    project = project or default_project.format(
        owner=owner, repository=repository, username=username
    )
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
    print(
        "Creating label "
        + dye(name, fg=color, bg=readable_text_color_on(color))
        + " ..."
    )
    repo.create_label(name=name, color=f"{color:6x}", **label_data)


def push_to_repo(
    auth_cache: Optional[str],
    body: str,
    title: Optional[str],
    repo: str,
    project: Optional[str],
    default_project: Optional[str],
    column: Optional[str],
    default_column: Optional[str],
    assign: list[str],
    self_assign: bool,
    milestone: Optional[str],
    tag: list[str],
    create_missing: bool,
    no_issue: bool,
    dry_run: bool,
    open: bool,
    **_,
) -> None:
    gh = login(auth_cache)
    repo_full_name = resolve_self_repository_shorthand(gh, repo)
    repo: Repository = gh.get_repo(repo_full_name)
    username = gh.get_user().login
    assignees = assign or ([username] if self_assign else [])
    project, column = resolve_defaults(
        column, project, default_project, default_column, repo_full_name, username
    )
    # user specified a name
    if project or column:
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
        if label is None:
            return
        labels.append(label)

    if milestone is not None:
        milestone: Milestone = search_for_object(
            repo.get_milestones(),
            milestone,
            create_missing=create_missing,
            object_name="milestone",
            create=lambda: repo.create_milestone(title=milestone),
            get_name=lambda obj: obj.title,
        )

        if milestone is None:
            return

    owner, repository = repo_full_name.split("/")

    if not no_issue:
        issue = None
        if not dry_run:
            issue = repo.create_issue(
                title=title or body,
                body=body if title else "",
                assignees=assignees,
                labels=tag,
                milestone=(milestone or github.GithubObject.NotSet),
            )
            card = column.create_card(content_id=issue.id, content_type="Issue")
            url = issue.html_url
        else:
            url = "N/A"

        print(
            make_github_issue_art(
                owner=owner,
                repository=repository,
                project=(project.name if project is not None else None),
                column=(column.name if column is not None else None),
                username=username,
                url=url,
                issue_number=(issue.number if issue is not None else "N/A"),
                labels=labels,
                body=body,
                title=title,
                assignees=assignees,
                milestone=(milestone.title if milestone is not None else None),
            )
        )

    else:
        if not dry_run:
            column.create_card(note=body)
            url = project.html_url
        else:
            url = "N/A"

        print(
            make_github_project_art(
                owner=owner,
                repository=repository,
                project=project,
                column=column,
                body=body,
                url=url,
            )
        )

    # Open project URL
    if open and url != "N/A":
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

    gh = login(auth_cache)
    user = gh.get_user()
    username = user.login
    # for some reason, we have to do this to get a NamedUser (not an AuthenticatedUser) to be able to call .get_projects()...
    project, column = get_project_and_column(
        gh.get_user(user.login), project, column, create_missing
    )

    if not column or not project:
        return

    print(
        f"Saving card in {dye(username, C_PRIMARY)} › {dye(project.name, C_PRIMARY)} › {dye(column.name, C_PRIMARY)}..."
    )

    if not dry_run:
        column.create_card(note=body)
        url = project.html_url
    else:
        url = "N/A"

    print(
        make_github_user_project_art(
            username=username,
            project=project.name,
            column=column.name,
            body=body,
            url=url,
        )
    )

    # Open project URL
    if open and url != "N/A":
        webbrowser.open(url)


T = TypeVar("T")


def search_for_object(
    objects: list[T],
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
            print(f"found {the_object!r}")
            break
    else:
        if create_missing and answered_yes_to(
            f"Create missing {object_name} {name!r}?"
        ):
            the_object = create()
        else:
            return

    # Not found and not created
    print(f"the object is {the_object!r}")
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
    print(f"create_missing is {create_missing!r}")
    project = search_for_object(
        repo.get_projects(),
        project_name,
        create_missing=create_missing,
        object_name="project",
        create=lambda: repo.create_project(
            name=project_name, body=ask_text("Enter the project's description..."),
        ),
    )
    print(f"project is {project!r}")

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


if __name__ == "__main__":
    import doctest

    doctest.testmod()
