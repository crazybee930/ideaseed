import os
import pprint
from os.path import dirname
import github
from github import Issue
from github.GithubException import BadCredentialsException, TwoFactorException
from ideaseed.utils import ask, dye, get_token_cache_filepath
from ideaseed.constants import C_PRIMARY
from typing import *
from github import Github
import json
from github.GithubException import TwoFactorException
import inquirer as q
from ideaseed.utils import ask


def login_with_cache() -> Optional[Github]:
    """
    Tries to login using the cached credentials.
    `None` is returned if the cache does not exist or is invalid.
    """
    if os.path.exists(get_token_cache_filepath('github')):
        with open(get_token_cache_filepath('github'), encoding="utf8") as file:
            creds = json.load(file)
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


def clear_auth_cache():
    if os.path.exists(get_token_cache_filepath('github')):
        os.remove(get_token_cache_filepath('github'))


def write_auth_cache(auth):
    os.makedirs(dirname(get_token_cache_filepath('github')), exist_ok=True)
    with open(get_token_cache_filepath('github'), "w", encoding="utf8") as file:
        json.dump(auth, file)


def login(args: Dict[str, Any], method: Optional[str] = None) -> Github:
    """
    Returns a `Github` instance to interact with.
    Prompts the user to login, either via username/password
    or using a Personal Access Token
    """
    gh = login_with_cache()
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
        q.Text(
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

    if not args["--no-auth-cache"]:
        write_auth_cache(answers)

    if answers["pat"] is not None:
        try:
            gh = Github(answers["pat"])
            github_username(gh)
            return gh
        except BadCredentialsException:
            print("Bad token")
            return login(args, method)
    else:
        try:
            gh = Github(answers["username"], answers["password"])
            github_username(gh)
            return gh
        except TwoFactorException:
            print(
                "Your account uses two-factor authentification. Please use a personal access token instead."
            )
            return login(args, method="Personal Access Token")
        except BadCredentialsException:
            print("Bad credentials")
            return login(args, method)


def github_username(gh: Github) -> str:
    return gh.get_user().login


def resolve_self_repository_shorthand(gh: Github, repo: str) -> str:
    if "/" not in repo:
        return github_username(gh) + "/" + repo
    return repo


def push_to_repo(args: Dict[str, Any]) -> None:
    gh = login(args)
    repo_name = resolve_self_repository_shorthand(gh, args["REPO"])
    idea = args["IDEA"]
    project_name = args["PROJECT"]
    column_name = args["COLUMN"]
    print(
        f"Saving card in {dye(repo_name, C_PRIMARY)}"
        f" › {dye(project_name, C_PRIMARY)}"
        f" › {dye(column_name, C_PRIMARY)}..."
    )
    repo = gh.get_repo(repo_name)

    project = None
    for p in repo.get_projects():
        if p.name.lower() == project_name.lower():
            project = p
            break

    # Project not found
    if project is None and args["--create-missing"]:
        if ask(q.Confirm("ans", message=f"Create missing project {project_name!r}?")):
            description: str = ask(
                q.Editor("ans", message="Enter the project's description...")
            )
            project = repo.create_project(name=project_name, body=description)
        else:
            return
    # Not found and not create
    elif project is None:
        print(dye(f"Error: project {project_name!r} does not exist!", fg=0xF00))
        return

    # Column
    column = None
    for c in project.get_columns():
        if c.name.lower() == column_name.lower():
            column = c
            break

    # Column not found
    if column is None and args["--create-missing"]:
        if ask(q.Confirm("ans", message=f"Create missing column {column_name!r}?")):
            column = project.create_column(column_name)
        else:
            return
    # Not found and not create
    elif column is None:
        print(dye(f"Error: column {column_name!r} does not exist!", fg=0xF00))
        return

    if args["--issue"]:
        issue = repo.create_issue(
            title=args["--title"] or idea,
            body=idea if args["--title"] else "",
            assignees=[github_username(gh)],
            labels=args["--tag"],
        )
        card = column.create_card(content_id=issue.id, content_type="Issue")
    else:
        card = column.create_card(note=idea)
        pass

def push_to_user(args: Dict[str, Any]) -> None:
    gh = login(args)
    idea = args["IDEA"]
    project_name: str = args["--user-project"]
    column_name: str = args["PROJECT"]
    print(
        f"Saving card in {dye(github_username(gh), C_PRIMARY)} › {dye(project_name, C_PRIMARY)} › {dye(column_name, C_PRIMARY)}..."
    )
    project = None
    user = gh.get_user()
    for p in user.get_projects():
        if p.name.lower() == project_name.lower():
            project = p
            break

    # Project not found
    if project_name is None and args["--create-missing"]:
        if ask(q.Confirm("ans", message=f"Create missing project {project_name!r}?")):
            description = ask(
                q.Editor("ans", message="Enter the project's description...")
            )
            project = user.create_project(name=project_name, body=description)
        else:
            return
    # Not found and not create
    elif project_name is None:
        print(dye(f"Error: project {project_name!r} does not exist!", fg=0xF00))
        return

    # Column
    column = None
    for c in project.get_columns():
        if c.name.lower() == column_name.lower():
            column = c
            break

    # Column not found
    if column_name is None and args["--create-missing"]:
        if ask(q.Confirm("ans", message=f"Create missing column {column_name!r}?")):
            column = project.create_column(column_name)
        else:
            return
    # Not found and not create
    elif column_name is None:
        print(dye(f"Error: column {column_name!r} does not exist!", fg=0xF00))
        return

    column.create_card(note=idea)
