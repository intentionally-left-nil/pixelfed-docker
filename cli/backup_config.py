from .service_config import ServiceConfig
from .config import Config
from .dirs import Dirs
from .template import fill_template


class BackupConfig(ServiceConfig):
    @classmethod
    def configure(cls, *, config: Config, secrets: Config):
        if not secrets.get(["backup", "bucket"]):
            secrets.set(
                ["backup", "bucket"],
                input("What bucket do you want to store the backups in? "),
            )
        if not secrets.get(["backup", "access_key"]):
            secrets.set(
                ["backup", "access_key"],
                input(
                    "What's the aws access key id (needs access to pixelfed and backups bucket)? "
                ),
            )
        if not secrets.get(["backup", "secret_access_key"]):
            secrets.set(
                ["backup", "secret_access_key"],
                input("What's the aws secret access key? "),
            )
        if not config.get(["backup", "max_db_backups"]):
            days = int(input("How many days worth of db backups do you want to keep? "))
            if days < 1:
                raise RuntimeError(f"{days} must be > 0")
            config.set(
                ["backup", "max_db_backups"],
                str(days),
            )
        if not config.get(["backup", "max_file_backups"]):
            days = int(
                input("How many days worth of file backups do you want to keep? ")
            )
            if days < 1:
                raise RuntimeError(f"{days} must be > 0")
            config.set(
                ["backup", "max_file_backups"],
                str(days),
            )

    @classmethod
    def update_files(cls, *, config: Config, secrets: Config, dirs: Dirs):
        fill_template(
            template=dirs.templates / "backup.env",
            dest=dirs.secrets / "backup" / ".env",
            config=config,
            secrets=secrets,
        )
