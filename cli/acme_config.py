from pathlib import Path

from .service_config import ServiceConfig
from .config import Config
from .dirs import Dirs
from .template import fill_template
import os
import subprocess
import re


class AcmeConfig(ServiceConfig):
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

    @classmethod
    def update_files(cls, *, config: Config, secrets: Config, dirs: Dirs):
        (dirs.secrets / "acme").mkdir(exist_ok=True)
        create_certs_dest = dirs.config / "create_certs" / "create_certs.sh"
        fill_template(
            template=dirs.templates / "create_certs.sh",
            dest=create_certs_dest,
            config=config,
            secrets=secrets,
        )
        create_certs_dest.chmod(0o755)

        made_changes = False

        with open(dirs.secrets / "acme" / "account.conf", "a", encoding="utf-8"):
            pass

        if not secrets.get(["acme", "upgrade_hash"]):
            made_changes = True
            child_environ = os.environ.copy()
            child_environ["acme_email"] = secrets.get(["acme", "email"]) or ""
            result = subprocess.run(
                [
                    "sudo",
                    "-E",
                    "docker-compose",
                    "--profile",
                    "setup",
                    "run",
                    "--rm",
                    "--build",
                    "acme",
                    "--info",
                ],
                env=child_environ,
                capture_output=True,
                check=True,
                timeout=60,
            )
            stdout = result.stdout.decode("utf-8")
            match = re.search(r"UPGRADE_HASH='(.*)'$", result.stdout.decode("utf-8"))
            if match == None:
                print(stdout)
                raise RuntimeError("Could not find UPGRADE_HASH in acme.sh --info")
            secrets.set(["acme", "upgrade_hash"], match.group(1))

        with open(dirs.secrets / "acme" / "account.conf", "w", encoding="utf-8") as f:
            f.write(
                "\n".join(
                    [
                        f"""ACCOUNT_EMAIL='{secrets.get(["acme", "email"])}'""",
                        f"""UPGRADE_HASH='{secrets.get(["acme", "upgrade_hash"])}'""",
                        "",
                    ]
                )
            )

        if not secrets.get(["acme", "account_thumbprint"]):
            made_changes = True
            result = subprocess.run(
                [
                    "sudo",
                    "docker-compose",
                    "--profile",
                    "setup",
                    "run",
                    "--rm",
                    "acme",
                    "--accountconf",
                    "/root/account.conf",
                    "--server",
                    "letsencrypt",
                    "--register-account",
                ],
                capture_output=True,
                check=True,
                timeout=30,
            )
            stdout = result.stdout.decode("utf-8")
            match = re.search(
                r"ACCOUNT_THUMBPRINT='(.*)'$", result.stdout.decode("utf-8")
            )
            if match == None:
                print(stdout)
                raise RuntimeError(
                    "Could not find ACCOUNT_THUMBPRINT in acme.sh --register-account"
                )
            secrets.set(["acme", "account_thumbprint"], match.group(1))

        if made_changes or not (dirs.secrets / "acme" / "backup.tar").exists():
            backup = subprocess.run(
                [
                    "sudo",
                    "docker-compose",
                    "--profile",
                    "setup",
                    "run",
                    "--rm",
                    "--entrypoint",
                    "/bin/tar",
                    "acme",
                    "c",
                    "-C",
                    "/root",
                    "-f",
                    "-",
                    ".acme.sh",
                ],
                capture_output=True,
                check=True,
                timeout=30,
            )
            with open(dirs.secrets / "acme" / "backup.tar", "wb") as f:
                f.write(backup.stdout)
