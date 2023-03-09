from pathlib import Path
from typing import Any
from .config import Config
from .service_config import ServiceConfig
from .ngrok_config import NgrokConfig
from .acme_config import AcmeConfig

from typing import Type


def configure():
    secrets = Config(Path("secrets", "config.toml"))
    secrets.load()
    configs: list[Type[ServiceConfig]] = [NgrokConfig, AcmeConfig]
    [config.configure(secrets) for config in configs]
    [
        config.update_files(
            secrets=secrets, template_dir=Path("templates"), secret_dir=Path("secrets")
        )
        for config in configs
    ]
    secrets.save()


def secrets_path():
    return Path("secrets", "config.toml")
