from pathlib import Path
from .dirs import Dirs
from .config import Config
from .service_config import ServiceConfig
from .ngrok_config import NgrokConfig
from .acme_config import AcmeConfig
from .nginx_config import NginxConfig

from typing import Type


def configure():
    dirs = Dirs(Path("."))
    config = Config(dirs.config / "config.toml")
    secrets = Config(dirs.secrets / "config.toml")
    config.load()
    secrets.load()

    configs: list[Type[ServiceConfig]] = [NgrokConfig, AcmeConfig, NginxConfig]
    [c.configure(config=config, secrets=secrets) for c in configs]
    [c.update_files(config=config, secrets=secrets, dirs=dirs) for c in configs]
    config.save()
    secrets.save()


def secrets_path():
    return Path("secrets", "config.toml")
