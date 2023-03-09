from pathlib import Path
import tomli
import tomli_w
from typing import Any, Optional


class Config:
    def __init__(self, path: Path):
        self.path = path
        self.config: Optional[dict[str, Any]] = None

    def load(self):
        try:
            with open(self.path, "rb") as f:
                self.config = tomli.load(f)
        except FileNotFoundError:
            self.config = {}

    def save(self):
        if self.config:
            with open(self.path, "wb") as f:
                tomli_w.dump(self.config, f)

    def get(self, paths: list[str]):
        if len(paths) == 0 or not self.config:
            return None
        return self.__get(self.config, paths)

    def set(self, paths: list[str], value: Any):
        if len(paths) == 0:
            return

        if not self.config:
            self.config = {}

        self.__set(self.config, paths, value)

    def flatten(self) -> dict[str, Any]:
        dest = {}
        if self.config:
            self.__flatten(self.config, "", dest)
        return dest

    @classmethod
    def __get(cls, config: dict[str, Any], paths: list[str]):
        if len(paths) == 0:
            return None
        key = paths[0]
        rest = paths[1:]
        if key not in config:
            return None
        if len(rest) == 0:
            return config[key]
        return cls.__get(config[key], rest)

    @classmethod
    def __set(cls, config: dict[str, Any], paths: list[str], value: Any):
        key = paths[0]
        rest = paths[1:]
        if len(rest) == 0:
            config[key] = value
            return
        if key not in config:
            config[key] = {}
        cls.__set(config[key], rest, value)

    @classmethod
    def __flatten(cls, config: dict[str, Any], prefix: str, dest: dict[str, Any]):
        for key, value in config.items():
            if isinstance(value, dict):
                cls.__flatten(value, f"{prefix}{key}.", dest)
            else:
                dest[f"{prefix}{key}"] = value
