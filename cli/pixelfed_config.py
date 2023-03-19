import re
import subprocess
from .service_config import ServiceConfig
from .config import Config
from .dirs import Dirs

from .template import fill_template
from .util import check_result


class PixelfedConfig(ServiceConfig):
    @classmethod
    def configure(cls, *, config: Config, secrets: Config):
        if not secrets.get(["pixelfed", "app_key"]):
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
