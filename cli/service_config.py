from pathlib import Path
from .config import Config
from .dirs import Dirs


class ServiceConfig:
    @classmethod
    def configure(cls, *, config: Config, secrets: Config):
        pass

    @classmethod
    def update_files(cls, *, config: Config, secrets: Config, dirs: Dirs):
        pass
