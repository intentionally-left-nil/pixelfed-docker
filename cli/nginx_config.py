from pathlib import Path
from urllib.parse import urlparse
import re
import subprocess

from .service_config import ServiceConfig
from .config import Config
from .dirs import Dirs
from .template import fill_template
from .util import check_result


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
            template=dirs.templates / "nginx.env",
            dest=dirs.secrets / "nginx" / ".env",
            config=config,
            secrets=secrets,
        )

        fill_template(
            template=dirs.templates / "nginx.conf",
            dest=dirs.config / "nginx" / "default.conf",
            config=config,
            secrets=secrets,
        )

        fill_template(
            template=dirs.templates / "nginx_ssl.conf",
            dest=dirs.config / "nginx" / "ssl.conf",
            config=config,
            secrets=secrets,
        )

        made_changes = False
        if not config.get(["acme", "account_thumbprint"]):
            made_changes = True
            acme_email = secrets.get(["acme", "email"]) or ""
            # Create the initial_acme_config.tar before running the container
            # otherwise docker will create a folder in its place
            with open(dirs.secrets / "nginx" / "initial_acme_config.tar", "wb"):
                pass

            result = subprocess.run(
                [
                    "sudo",
                    "docker-compose",
                    "--profile",
                    "prod",
                    "run",
                    "--rm",
                    "--entrypoint",
                    "/bin/sh",
                    "nginx",
                    "-c",
                    f'''curl https://get.acme.sh | sh -s email="{acme_email}"''',
                ],
                timeout=60,
            )
            check_result(result)

            result = subprocess.run(
                [
                    "sudo",
                    "docker-compose",
                    "--profile",
                    "prod",
                    "run",
                    "--rm",
                    "--entrypoint",
                    "/root/.acme.sh/acme.sh",
                    "nginx",
                    "--server",
                    "letsencrypt",
                    "--register-account",
                ],
                capture_output=True,
                timeout=30,
            )
            check_result(result)
            stdout = result.stdout.decode("utf-8")
            match = re.search(
                r"ACCOUNT_THUMBPRINT='(.*)'$", result.stdout.decode("utf-8")
            )
            if match == None:
                print(stdout)
                raise RuntimeError(
                    "Could not find ACCOUNT_THUMBPRINT in acme.sh --register-account"
                )
            config.set(["acme", "account_thumbprint"], match.group(1))

            # Need to generate the template again, with the new certificate
            fill_template(
                template=dirs.templates / "nginx.conf",
                dest=dirs.config / "nginx" / "default.conf",
                config=config,
                secrets=secrets,
            )
        if (
            made_changes
            or not (dirs.secrets / "nginx" / "initial_acme_config.tar").exists()
        ):
            result = subprocess.run(
                [
                    "sudo",
                    "docker-compose",
                    "--profile",
                    "prod",
                    "run",
                    "--rm",
                    "--entrypoint",
                    "/bin/tar",
                    "nginx",
                    "c",
                    "-C",
                    "/root",
                    "-f",
                    "-",
                    ".acme.sh",
                ],
                capture_output=True,
                timeout=30,
            )
            check_result(result)

            with open(dirs.secrets / "nginx" / "initial_acme_config.tar", "wb") as f:
                f.write(result.stdout)
