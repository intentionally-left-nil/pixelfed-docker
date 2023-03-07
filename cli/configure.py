from pathlib import Path
from typing import Any
from .config import Config
from .ngrok_config import NgrokConfig


def configure():
    secrets = Config(Path("secrets", "config.toml"))
    secrets.load()
    NgrokConfig.configure(secrets)
    secrets.save()
    NgrokConfig.update_files(
        secrets=secrets, template_dir=Path("templates"), secret_dir=Path("secrets")
    )


def secrets_path():
    return Path("secrets", "config.toml")
