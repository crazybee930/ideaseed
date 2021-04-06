import json
from pathlib import Path
from typing import Any, Tuple, TypeVar

from rich import print

T = TypeVar("T")


class Cache:
    def __init__(self, path: Path, service: str):
        self.path = path
        self.service = service
        self.cache = self.read()

    def create(self):
        self.path.parent.mkdir(parents=True, exists_ok=True)
        self.path.touch()

    @contextmanager
    def modify(self):
        """
        Context manager that reads from the cache file, executes the given function, and writes back the result.
        """
        with open(self.path, "r") as file:
            self.cache = json.load(file)

        yield

        with open(self.path, "w") as file:
            json.dump(self.cache, file)

    def write(self, data: dict[str, Any]):
        with self.modify():
            self.cache |= data

    def read(self) -> dict[str, Any]:
        if self.cache:
            return self.cache
        with open(self.path, "r") as file:
            self.cache = json.load(file).get(self.service, {})
            return self.cache

    def clear(self, old_cache: dict[str, Any]):
        with self.modify():
            del self.cache[self.service]

    def clear_all(self):
        self.path.unlink(missing_ok=True)

    def login(self,) -> T:
        print(f"Logging into [blue bold]{self.service}[/]...")
        if (cache := self.read()) :
            return self.login_from_cache()

        loggedin, cache_data = self.login_manually(self)
        self.write(cache_data)
        return loggedin

    def login_manually(self, **credentials) -> Tuple[T, dict[str, Any]]:
        raise NotImplementedError("Please implement login_manually in your subclass.")

    def login_from_cache(self) -> T:
        raise NotImplementedError(
            "Please implement login_with_credentials in your subclass."
        )
