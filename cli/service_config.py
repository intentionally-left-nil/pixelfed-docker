from pathlib import Path
from .config import Config


class ServiceConfig:
    @classmethod
    def configure(cls, secrets: Config):
        pass

    @classmethod
    def update_files(cls, secrets: Config, template_dir: Path, secret_dir: Path):
        pass
