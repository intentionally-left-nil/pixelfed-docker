from secrets import choice
import string
from .service_config import ServiceConfig
from .config import Config
from .dirs import Dirs
from .template import fill_template


class DatabaseConfig(ServiceConfig):
    @classmethod
    def configure(cls, *, config: Config, secrets: Config):
        if not secrets.get(["db", "password"]):
            password = "".join(
                choice(string.ascii_letters + string.digits) for i in range(32)
            )
            secrets.set(["db", "password"], password)

    @classmethod
    def update_files(cls, *, config: Config, secrets: Config, dirs: Dirs):
        fill_template(
            template=dirs.templates / "db.env",
            dest=dirs.secrets / "db" / ".env",
            config=config,
            secrets=secrets,
        )
