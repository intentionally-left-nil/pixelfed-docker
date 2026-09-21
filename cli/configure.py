import difflib
import sys
import tempfile
from pathlib import Path
from .dirs import Dirs
from .config import Config
from .service_config import ServiceConfig
from .database_config import DatabaseConfig
from .pixelfed_config import PixelfedConfig
from .backup_config import BackupConfig

from typing import Type


def configure(*, dry_run: bool = False, apply_only: bool = False):
    dirs = Dirs(Path("."))
    config = Config(dirs.config / "config.toml")
    secrets = Config(dirs.secrets / "config.toml")
    config.load()
    secrets.load()

    configs: list[Type[ServiceConfig]] = [
        DatabaseConfig,
        PixelfedConfig,
        BackupConfig,
    ]

    if dry_run:
        dry_run_configure(config=config, secrets=secrets, dirs=dirs, configs=configs)
        return

    if apply_only:
        # Re-render the real output files from the existing config/secrets.
        # No prompts, and config.toml/secrets/config.toml are never touched.
        [c.update_files(config=config, secrets=secrets, dirs=dirs) for c in configs]
        print(
            "Applied: regenerated the templated files from the existing "
            "config/config.toml and secrets/config.toml. Neither toml file "
            "was modified, and you were not prompted for anything."
        )
        return

    # Special case
    PixelfedConfig.generate_pixelfed_secrets(secrets=secrets, dirs=dirs)

    [c.configure(config=config, secrets=secrets) for c in configs]
    [c.update_files(config=config, secrets=secrets, dirs=dirs) for c in configs]
    config.save()
    secrets.save()


def dry_run_configure(
    *,
    config: Config,
    secrets: Config,
    dirs: Dirs,
    configs: list[Type[ServiceConfig]],
):
    """Render every template into a scratch directory using the *existing*
    config/secrets (no prompts, nothing on disk is touched), then print a
    unified diff against what's really on disk today. Intended to validate
    that update_files() would produce the files you expect before actually
    running the interactive scaffold.
    """
    print("DRY RUN: no files will be written, no prompts will be shown.\n")
    with tempfile.TemporaryDirectory(prefix="pixelfed-docker-dry-run-") as tmp:
        tmp_root = Path(tmp)
        scratch_dirs = Dirs(
            dirs.root,
            config=tmp_root / "config",
            templates=dirs.templates,
            secrets=tmp_root / "secrets",
        )

        for c in configs:
            c.update_files(config=config, secrets=secrets, dirs=scratch_dirs)

        any_diff = False
        for generated, real_root in (
            (scratch_dirs.config, dirs.config),
            (scratch_dirs.secrets, dirs.secrets),
        ):
            if not generated.exists():
                continue
            for generated_file in sorted(generated.rglob("*")):
                if generated_file.is_dir():
                    continue
                rel = generated_file.relative_to(generated)
                real_file = real_root / rel
                new_text = generated_file.read_text(encoding="utf-8")
                old_text = (
                    real_file.read_text(encoding="utf-8") if real_file.exists() else ""
                )
                if new_text == old_text:
                    continue
                any_diff = True
                diff = difflib.unified_diff(
                    old_text.splitlines(keepends=True),
                    new_text.splitlines(keepends=True),
                    fromfile=f"a/{real_file}",
                    tofile=f"b/{real_file}",
                )
                sys.stdout.writelines(diff)
                print()

        if not any_diff:
            print("No differences: regenerating now would change nothing.")



def secrets_path():
    return Path("secrets", "config.toml")
