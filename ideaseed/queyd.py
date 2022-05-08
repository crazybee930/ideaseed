import json
from pathlib import Path
from subprocess import call
from typing import Any, Callable, NamedTuple, Tuple

import requests
from requests.models import Response
from rich.prompt import InvalidResponse

from ideaseed import ui
from ideaseed.authentication import Cache, T
from ideaseed.ondisk import Idea
from ideaseed.utils import ask

"""
curl 'http://localhost:8000/' -H 'Accept-Encoding: gzip, deflate, br' -H 'Content-Type: application/json' -H 'Accept: application/json' -H 'Connection: keep-alive' -H 'DNT: 1' -H 'Origin: http://localhost:8000' --data-binary '{"query":"query {\n  notes {\n    id, title\n  }\n}"}' --compressed
"""


def _to_gql(query: dict[str, Any] | list[str]) -> str:
    if isinstance(query, dict):
        return "\n".join(
            f"{key} {{ {_to_gql(value)} }}" for key, value in query.items()
        )
    elif isinstance(query, list):
        return ", ".join(map(str, query))
    return ""


def _gql_call(name: str, **arguments) -> str:
    return f"{name}({', '.join(f'{key}: {json.dumps(value)}' for key, value in arguments.items())})"


class QueydClient(NamedTuple):
    query: Callable[[dict[str, Any]], Response]
    mutation: Callable[[dict[str, Any]], Response]

    @classmethod
    def authenticated(cls, auth_token: str, endpoint: str) -> "QueydClient":
        return cls(
            query=lambda query: requests.post(
                endpoint,
                json={"query": _to_gql({"query": query})},
                headers={"Authentication": f"Bearer {auth_token}"},
            ),
            mutation=lambda mutation: requests.post(
                endpoint,
                json={"query": _to_gql({"mutation": mutation})},
                headers={"Authentication": f"Bearer {auth_token}"},
            ),
        )

    def add(self, idea: Idea) -> Response:
        return self.mutation(
            {
                _gql_call(
                    "add",
                    title=idea.title,
                    project=idea.project,
                    body=idea.body,
                    tags=idea.labels,
                ): ["id"]
            }
        )


def is_correct_password(password: str, endpoint: str) -> bool:
    client = QueydClient.authenticated(password, endpoint)
    response = client.query({"notes": {"id"}})
    if response.status_code == 403:
        return False
    if response.status_code // 100 <= 2:
        return True
    raise Exception(
        f"Unexpected status code: {response.status_code}. Response is: {response.text}"
    )


class AuthCache(Cache):

    graphql_endpoint: str

    def __init__(self, path: Path, graphql_endpoint: str):
        self.graphql_endpoint = graphql_endpoint
        super().__init__(path, "queyd")

    def login_from_cache(self) -> QueydClient:
        return QueydClient.authenticated(
            self.cache["token"], endpoint=self.graphql_endpoint
        )

    def login_manually(self, **params) -> Tuple[Any, dict[str, Any]]:
        def _validate(ans: str) -> bool:
            if not is_correct_password(ans, self.graphql_endpoint):
                raise InvalidResponse("Incorrect password")
            return True

        cache = {
            "token": ask(
                "Password",
                is_valid=_validate,
                password=True,
            )
        }
        return QueydClient.authenticated(cache["token"], self.graphql_endpoint), cache


def using() -> bool:
    return True
