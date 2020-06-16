import os
from os.path import dirname
import github
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
    if os.path.exists(get_token_cache_filepath()):
        with open(get_token_cache_filepath(), encoding="utf8") as file:
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
    if os.path.exists(get_token_cache_filepath()):
        os.remove(get_token_cache_filepath())


def write_auth_cache(auth):
    os.makedirs(dirname(get_token_cache_filepath()), exist_ok=True)
    with open(get_token_cache_filepath(), "w", encoding="utf8") as file:
        json.dump(auth, file)


def login(method: Optional[str] = None) -> Github:
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

    write_auth_cache(answers)

    if answers["pat"] is not None:
        try:
            gh = Github(answers["pat"])
            github_username(gh)
            return gh
        except BadCredentialsException:
            print("Bad token")
            return login(method)
    else:
        try:
            gh = Github(answers["username"], answers["password"])
            github_username(gh)
            return gh
        except TwoFactorException:
            print(
                "Your account uses two-factor authentification. Please use a personal access token instead."
            )
            return login(method="Personal Access Token")
        except BadCredentialsException:
            print("Bad credentials")
            return login(method)


def github_username(gh: Github) -> str:
    return gh.get_user().login


def resolve_self_repository_shorthand(gh: Github, repo: str) -> str:
    if "/" not in repo:
        return github_username(gh) + "/" + repo
    return repo


def push_to_repo(args: Dict[str, Any]) -> None:
    gh = login()
    repo = resolve_self_repository_shorthand(gh, args["REPO"])
    idea = args["IDEA"]
    project = args["PROJECT"]
    column = args["COLUMN"]
    print(
        f"Saving card in {dye(repo, C_PRIMARY)} › {dye(project, C_PRIMARY)} › {dye(column, C_PRIMARY)}..."
    )


def push_to_user(args: Dict[str, Any]) -> None:
    gh = login()
    idea = args["IDEA"]
    project = args['REPO']
    column = args['PROJECT']
    print(
        f"Saving card in {dye(github_username(gh), C_PRIMARY)} › {dye(project, C_PRIMARY)} › {dye(column, C_PRIMARY)}..."
    )
    pass
