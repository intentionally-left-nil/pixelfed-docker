from pathlib import Path
from typing import Any
from .config import Config
from .ngrok_config import NgrokConfig


def configure():
    secrets = Config(Path("secrets", "config.toml"))
    secrets.load()
    NgrokConfig.configure(secrets)
    secrets.save()


def secrets_path():
    return Path("secrets", "config.toml")
