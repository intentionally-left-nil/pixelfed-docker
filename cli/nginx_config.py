from pathlib import Path
from urllib.parse import urlparse
import re
import subprocess

from .service_config import ServiceConfig
from .config import Config
from .dirs import Dirs
from .template import fill_template
from .util import check_result, docker_compose_prefix


class NginxConfig(ServiceConfig):
    @classmethod
    def configure(cls, *, config: Config, secrets: Config):
        if not secrets.get(["acme", "email"]):
            print(
                "Lets Encrypt (via acme.sh) is used to set up a free SSL certificate for your domain"
            )
            secrets.set(
                ["acme", "email"],
                input(
                    "What (public) email do you want to register your certificate with? "
                ),
            )
        if not config.get(["domain", "web"]):
            response = input("What domain name do you want to use for your site? ")
            url = response if "://" in response else "http://" + response
            domain = urlparse(url).hostname
            if domain is None:
                raise RuntimeError("Invalid domain")

            config.set(["domain", "web"], domain)

        if not config.get(["domain", "web_alias"]):
            domain = (config.get(["domain", "web"]) or "").removeprefix("www")
            print(f"Do you want website visitors to prefer {domain} or www.{domain}?")
            if choice := input(f"Prefer {domain} (y/n)? ").lower() == "y":
                config.set(["domain", "web"], domain)
                config.set(["domain", "web_alias"], f"www.{domain}")
            elif choice == "n":
                config.set(["domain", "web"], f"www.{domain}")
                config.set(["domain", "web_alias"], domain)
            else:
                raise RuntimeError("Invalid choice y/n")

    @classmethod
    def update_files(cls, *, config: Config, secrets: Config, dirs: Dirs):
        fill_template(
            template=dirs.templates / "nginx.conf",
            dest=dirs.config / "nginx" / "default.conf",
            config=config,
            secrets=secrets,
        )

        fill_template(
            template=dirs.templates / "nginx_dev.conf",
            dest=dirs.config / "nginx_dev" / "default.conf",
            config=config,
            secrets=secrets,
        )

        fill_template(
            template=dirs.templates / "proxy.json",
            dest=dirs.secrets / "nginx" / "proxy.json",
            config=config,
            secrets=secrets,
        )

        try:
            (dirs.config / "nginx" / "pixelfed").absolute().symlink_to(
                (dirs.root / "pixelfed").absolute(), target_is_directory=True
            )
        except FileExistsError:
            pass
