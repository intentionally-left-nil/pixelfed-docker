import re
from .service_config import ServiceConfig
from .config import Config
from .dirs import Dirs


class PixelfedConfig(ServiceConfig):
    @classmethod
    def configure(cls, *, config: Config, secrets: Config):
        pass

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
