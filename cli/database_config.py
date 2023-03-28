from .service_config import ServiceConfig
from .config import Config
from .dirs import Dirs
from .template import fill_template
from .util import generate_password


class DatabaseConfig(ServiceConfig):
    @classmethod
    def configure(cls, *, config: Config, secrets: Config):
        if not secrets.get(["db", "password"]):
            password = generate_password(length=32)
            secrets.set(["db", "password"], password)

        if not secrets.get(["db", "backup", "endpoint_url"]):
            url = input(
                "What s3 endpoint do you want to use for backing up the database? "
            )
            url = url if "://" in url else "https://" + url
            secrets.set(["db", "backup", "endpoint_url"], url)
        if not secrets.get(["db", "backup", "access_key"]):
            secrets.set(
                ["db", "backup", "access_key"],
                input("What's the aws access key id? "),
            )
        if not secrets.get(["db", "backup", "secret_access_key"]):
            secrets.set(
                ["db", "backup", "secret_access_key"],
                input("What's the aws secret access key? "),
            )
        if not secrets.get(["db", "backup", "region"]):
            secrets.set(
                ["db", "backup", "region"],
                input("What's the aws region? "),
            )
        if not secrets.get(["db", "backup", "bucket"]):
            secrets.set(
                ["db", "backup", "bucket"],
                input("What bucket do you want to store the backups in? "),
            )
        if not config.get(["db", "backup", "max_backups"]):
            days = int(input("How many days worth of db backups do you want to keep? "))
            if days < 1:
                raise RuntimeError(f"{days} must be > 0")
            config.set(
                ["db", "backup", "max_backups"],
                str(days),
            )

    @classmethod
    def update_files(cls, *, config: Config, secrets: Config, dirs: Dirs):
        fill_template(
            template=dirs.templates / "db.env",
            dest=dirs.secrets / "db" / ".env",
            config=config,
            secrets=secrets,
        )
        fill_template(
            template=dirs.templates / "db_backup.env",
            dest=dirs.secrets / "db_backup" / ".env",
            config=config,
            secrets=secrets,
        )
