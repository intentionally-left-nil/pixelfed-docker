from pathlib import Path


class Dirs:
    def __init__(self, root: Path):
        self.root = root
        self.config = root / "config"
        self.templates = root / "templates"
        self.secrets = root / "secrets"
