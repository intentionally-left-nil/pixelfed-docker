import re
import subprocess
from .service_config import ServiceConfig
from .config import Config
from .dirs import Dirs

from .template import fill_template
from .util import check_result, generate_password


class PixelfedConfig(ServiceConfig):
    @classmethod
    def configure(cls, *, config: Config, secrets: Config):
        if not config.get(["pixelfed", "max_size_mb"]):
            max_size = int(input("How many MB do you want to limit photo sizes to? "))
            config.set(["pixelfed", "max_size_mb"], str(max_size))
        if not secrets.get(["pixelfed", "admin", "user_name"]):
            secrets.set(
                ["pixelfed", "admin", "user_name"],
                input("What's the admin's username? "),
            )
        if not secrets.get(["pixelfed", "admin", "email"]):
            secrets.set(
                ["pixelfed", "admin", "email"],
                input("What's the admin's email? "),
            )
        if not secrets.get(["pixelfed", "admin", "display_name"]):
            secrets.set(
                ["pixelfed", "admin", "display_name"],
                input("What's the admin's display name? "),
            )
        if not secrets.get(["pixelfed", "admin", "password"]):
            secrets.set(["pixelfed", "admin", "password"], generate_password(length=32))
        if not secrets.get(["pixelfed", "app_key"]):
            subprocess.run(
                ["sudo", "docker-compose", "--profile", "setup", "build", "pixelfed"],
                check=True,
            )
            result = subprocess.run(
                [
                    "sudo",
                    "docker-compose",
                    "--profile",
                    "dev",
                    "run",
                    "--rm",
                    "--no-deps",
                    "app_dev",
                    "php",
                    "artisan",
                    "key:generate",
                    "--show",
                    "--no-ansi",
                ],
                capture_output=True,
                timeout=10,
            )
            check_result(result)
            app_key = result.stdout.decode("utf-8").strip()
            secrets.set(["pixelfed", "app_key"], app_key)

        if not secrets.get(["pixelfed", "oauth_private_key"]):
            subprocess.run(
                ["sudo", "docker-compose", "--profile", "setup", "build", "pixelfed"],
                check=True,
            )
            result = subprocess.run(
                [
                    "sudo",
                    "docker-compose",
                    "--profile",
                    "dev",
                    "run",
                    "--rm",
                    "--no-deps",
                    "app_dev",
                    "/bin/sh",
                    "-c",
                    "php artisan passport:keys -q --force && cat /var/www/storage/oauth-private.key && echo '' && cat /var/www/storage/oauth-public.key && rm /var/www/storage/oauth-public.key && rm /var/www/storage/oauth-private.key",
                ],
                capture_output=True,
                timeout=10,
            )
            check_result(result)
            output = result.stdout.decode("utf-8").strip().replace("\r", "")
            match = re.match(
                r"^.*BEGIN RSA PRIVATE KEY(?:.|\s)*?END RSA PRIVATE KEY.*$",
                output,
                re.MULTILINE,
            )
            if match is None:
                print(output)
                print(result.stderr)
                raise RuntimeError(
                    "Could not find RSA PRIVATE KEY after running passport:keys"
                )
            secrets.set(["pixelfed", "oauth_private_key"], match.group(0))
            match = re.search(
                r"^.*BEGIN PUBLIC KEY(?:.|\s)*?END PUBLIC KEY.*$",
                output,
                re.MULTILINE,
            )
            if match is None:
                print(output)
                print(result.stderr)
                raise RuntimeError(
                    "Could not find PUBLIC KEY after running passport:keys"
                )
            secrets.set(["pixelfed", "oauth_public_key"], match.group(0))

    @classmethod
    def update_files(cls, *, config: Config, secrets: Config, dirs: Dirs):
        source = dirs.root / "pixelfed" / "contrib" / "docker" / "Dockerfile.apache"
        with open(source, mode="r", encoding="utf-8") as f:
            dockerfile = f.read()
            enable_pg = re.compile(r"^\s*#(.*(?:libpq-dev|pdo_pgsql).*)$", re.MULTILINE)
            dockerfile = enable_pg.sub(r"\1", dockerfile)
            dockerfile = dockerfile.replace("pdo_sqlite ", "")

            dest = dirs.config / "pixelfed" / "Dockerfile"
            dest.parent.mkdir(exist_ok=True)

            with open(dest, "w", encoding="utf-8") as f:
                f.write(dockerfile)

        fill_template(
            template=dirs.templates / "pixelfed_dev.env",
            dest=dirs.secrets / "pixelfed" / "dev.env",
            config=config,
            secrets=secrets,
        )
        fill_template(
            template=dirs.templates / "pixelfed_init.env",
            dest=dirs.secrets / "pixelfed" / "init.env",
            config=config,
            secrets=secrets,
        )

        fill_template(
            template=dirs.templates / "php.ini",
            dest=dirs.config / "pixelfed" / "php.ini",
            config=config,
            secrets=secrets,
        )
