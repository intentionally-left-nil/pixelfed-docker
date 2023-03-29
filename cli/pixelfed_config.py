import re
import subprocess
from .service_config import ServiceConfig
from .config import Config
from .dirs import Dirs

from .template import fill_template
from .util import check_result, generate_password, docker_compose_prefix


class PixelfedConfig(ServiceConfig):
    @classmethod
    def generate_pixelfed_secrets(cls, *, secrets: Config, dirs: Dirs):
        # Hacks galore: This config requires getting the pixelfed image built first
        # so we need to bootstrap the stuff normally run during update_files
        # Revisit this in the future to better handle this special case.
        if not secrets.get(["pixelfed", "app_key"]):
            create_dockerfile(dirs)
            generate_empty_docker_env_files(dirs)
            subprocess.run(
                docker_compose_prefix() + ["--profile", "setup", "build", "pixelfed"],
                check=True,
            )
            result = subprocess.run(
                docker_compose_prefix()
                + [
                    "--profile",
                    "setup",
                    "run",
                    "--rm",
                    "--no-deps",
                    "--entrypoint",
                    "/bin/sh",
                    "pixelfed",
                    "-c",
                    "php artisan key:generate --show --no-ansi",
                ],
                capture_output=True,
                timeout=10,
            )
            check_result(result)
            app_key = result.stdout.decode("utf-8").strip()
            secrets.set(["pixelfed", "app_key"], app_key)

        if not secrets.get(["pixelfed", "oauth_private_key"]):
            create_dockerfile(dirs)
            generate_empty_docker_env_files(dirs)
            subprocess.run(
                docker_compose_prefix() + ["--profile", "setup", "build", "pixelfed"],
                check=True,
            )
            result = subprocess.run(
                docker_compose_prefix()
                + [
                    "--profile",
                    "setup",
                    "run",
                    "--rm",
                    "--no-deps",
                    "--entrypoint",
                    "/bin/sh",
                    "pixelfed",
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
        pass

    @classmethod
    def configure(cls, *, config: Config, secrets: Config):
        if not secrets.get(["pixelfed", "salt"]):
            secrets.set(["pixelfed", "salt"], generate_password(128))

        if not secrets.get(["pixelfed", "s3", "endpoint_url"]):
            url = input(
                "What s3 endpoint do you want to use to store your pixelfed files? "
            )
            url = url if "://" in url else "https://" + url
            secrets.set(["pixelfed", "s3", "endpoint_url"], url)
        if not secrets.get(["pixelfed", "s3", "region"]):
            secrets.set(
                ["pixelfed", "s3", "region"],
                input("What's the aws region? "),
            )
        if not secrets.get(["pixelfed", "s3", "access_key"]):
            secrets.set(
                ["pixelfed", "s3", "access_key"],
                input("What's the aws access key id? "),
            )
        if not secrets.get(["pixelfed", "s3", "secret_access_key"]):
            secrets.set(
                ["pixelfed", "s3", "secret_access_key"],
                input("What's the aws secret access key? "),
            )
        if not secrets.get(["pixelfed", "s3", "bucket"]):
            secrets.set(
                ["pixelfed", "s3", "bucket"],
                input("What bucket do you want to store your pixelfed files in? "),
            )
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

    @classmethod
    def update_files(cls, *, config: Config, secrets: Config, dirs: Dirs):
        create_dockerfile(dirs)
        fill_template(
            template=dirs.templates / "pixelfed_dev.env",
            dest=dirs.secrets / "pixelfed" / "dev.env",
            config=config,
            secrets=secrets,
        )
        fill_template(
            template=dirs.templates / "pixelfed.env",
            dest=dirs.secrets / "pixelfed" / ".env",
            config=config,
            secrets=secrets,
            overwrite_if_exists=False,
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

        fill_template(
            template=dirs.templates / "php-development.ini",
            dest=dirs.config / "pixelfed" / "php-development.ini",
            config=config,
            secrets=secrets,
        )


def create_dockerfile(dirs: Dirs):
    source = dirs.root / "pixelfed" / "contrib" / "docker" / "Dockerfile.fpm"
    with open(source, mode="r", encoding="utf-8") as f:
        dockerfile = f.read()
        enable_pg = re.compile(r"^\s*#(.*(?:libpq-dev|pdo_pgsql).*)$", re.MULTILINE)
        dockerfile = enable_pg.sub(r"\1", dockerfile)
        dockerfile = dockerfile.replace("pdo_sqlite ", "")
        dockerfile = dockerfile.replace(
            "ARG DEBIAN_FRONTEND=noninteractive",
            "ARG DEBIAN_FRONTEND=noninteractive\nRUN deluser www-data || true\nRUN delgroup www-data || true\nRUN addgroup --gid 1000 www-data && adduser --uid 1000 --gid 1000 --disabled-password --no-create-home www-data",
        )

        dest = dirs.config / "pixelfed" / "Dockerfile"
        dest.parent.mkdir(exist_ok=True)

        with open(dest, "w", encoding="utf-8") as f:
            f.write(dockerfile)


def generate_empty_docker_env_files(dirs: Dirs):
    files = [
        dirs.secrets / "nginx" / ".env",
        dirs.secrets / "pixelfed" / "dev.env",
        dirs.secrets / "pixelfed" / "init.env",
        dirs.secrets / "db" / ".env",
        dirs.secrets / "db_backup" / ".env",
    ]

    for file in files:
        file.parent.mkdir(parents=True, exist_ok=True)

        with open(file, "a") as f:
            # Create the file if it doesn't already exist
            pass
