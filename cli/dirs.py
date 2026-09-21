from pathlib import Path
from typing import Optional


class Dirs:
    def __init__(
        self,
        root: Path,
        *,
        config: Optional[Path] = None,
        templates: Optional[Path] = None,
        secrets: Optional[Path] = None,
    ):
        self.root = root
        self.config = config or root / "config"
        self.templates = templates or root / "templates"
        self.secrets = secrets or root / "secrets"
