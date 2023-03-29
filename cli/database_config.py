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

    @classmethod
    def update_files(cls, *, config: Config, secrets: Config, dirs: Dirs):
        fill_template(
            template=dirs.templates / "db.env",
            dest=dirs.secrets / "db" / ".env",
            config=config,
            secrets=secrets,
        )
