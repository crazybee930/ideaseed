import json
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Tuple, TypeVar

from rich import print

T = TypeVar("T")


class Cache:
    def __init__(self, path: Path, service: str):
        if not isinstance(path, Path):
            raise TypeError("Please use a Path for the `path` argument.")
        self.path = path
        self.service = service
        self.create()
        self.cache = self.read()

    def read(self) -> dict[str, Any]:
        with open(self.path, "r") as file:
            self.cache = json.load(file).get(self.service, {})
        return self.cache

    def create(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not (self.path.exists() and self.path.read_text() != ""):
            self.path.write_text("{}")

    @contextmanager
    def modify(self):
        """
        Context manager that reads from the cache file (into `self.cache`), executes the given function, and writes back the result (from `self.cache`).
        """
        with open(self.path, "r") as file:
            self.cache = json.load(file)

        yield

        with open(self.path, "w") as file:
            json.dump(self.cache, file)

    def write(self, data: dict[str, Any]):
        with self.modify():
            self.cache |= {self.service: data}

    def clear(self):
        print(f"[black on yellow]Clearing [bold]{self.service}[/bold] cache...")
        with self.modify():
            del self.cache[self.service]

    def clear_all(self):
        self.path.unlink(missing_ok=True)

    def login(self) -> Any:
        print(
            f"[dim][black]Logging into [/black][blue bold]{self.service}[/][black]..."
        )
        if self.cache:
            return self.login_from_cache()

        loggedin, cache_data = self.login_manually()
        self.write(cache_data)
        print("[dim]Logged in.")
        return loggedin

    def login_manually(self, **params) -> Tuple[Any, dict[str, Any]]:
        raise NotImplementedError("Please implement login_manually in your subclass.")

    def login_from_cache(self) -> Any:
        raise NotImplementedError("Please implement login_from_cache in your subclass.")
