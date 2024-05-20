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
            generate_empty_docker_env_files(dirs)
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
            generate_empty_docker_env_files(dirs)
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
                input("What bucket do you want to store your PROD pixelfed files in? "),
            )
        if not secrets.get(["pixelfed", "s3", "aws_url"]):
            endpoint_url: str = str(secrets.get(["pixelfed", "s3", "endpoint_url"]))
            bucket = secrets.get(["pixelfed", "s3", "bucket"])
            protocol, domain = endpoint_url.split("://", maxsplit=1)
            default_aws_url = f"{protocol}://{bucket}.{domain}"

            aws_url = input(
                f"What do you want to use for your PROD AWS_URL? Default: {default_aws_url}"
            )
            if not aws_url.strip():
                aws_url = default_aws_url
            secrets.set(["pixelfed", "s3", "aws_url"], default_aws_url)
        if not secrets.get(["pixelfed", "s3", "dev_access_key"]):
            secrets.set(
                ["pixelfed", "s3", "dev_access_key"],
                input("What's the aws access key id to access your DEV bucket? "),
            )
        if not secrets.get(["pixelfed", "s3", "dev_secret_access_key"]):
            secrets.set(
                ["pixelfed", "s3", "dev_secret_access_key"],
                input("What's the aws secret access key to access your DEV bucket? "),
            )
        if not secrets.get(["pixelfed", "s3", "dev_bucket"]):
            secrets.set(
                ["pixelfed", "s3", "dev_bucket"],
                input("What bucket do you want to store your DEV pixelfed files in? "),
            )
        if not secrets.get(["pixelfed", "s3", "dev_aws_url"]):
            endpoint_url: str = str(secrets.get(["pixelfed", "s3", "endpoint_url"]))
            bucket = secrets.get(["pixelfed", "s3", "dev_bucket"])
            protocol, domain = endpoint_url.split("://", maxsplit=1)
            default_aws_url = f"{protocol}://{bucket}.{domain}"

            aws_url = input(
                f"What do you want to use for your DEV AWS_URL? Default: {default_aws_url}"
            )
            if not aws_url.strip():
                aws_url = default_aws_url
            secrets.set(["pixelfed", "s3", "dev_aws_url"], default_aws_url)
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
