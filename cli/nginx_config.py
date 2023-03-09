from pathlib import Path
from urllib.parse import urlparse

from .service_config import ServiceConfig
from .config import Config
from .dirs import Dirs
from .template import fill_template


class NginxConfig(ServiceConfig):
    @classmethod
    def configure(cls, *, config: Config, secrets: Config):
        if not config.get(["domain"]):
            response = input("What domain name do you want to use for your site? ")
            url = response if "://" in response else "http://" + response
            config.set(["domain"], urlparse(url).hostname)

    @classmethod
    def update_files(cls, *, config: Config, secrets: Config, dirs: Dirs):
        fill_template(
            template=dirs.templates / "nginx.conf",
            dest=dirs.secrets / "nginx" / "default.conf",
            config=config,
            secrets=secrets,
        )
