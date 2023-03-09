from pathlib import Path

from .config import Config


def fill_template(*, template: Path, dest: Path, config: Config, secrets: Config):
    output = ""
    with open(template, mode="r", encoding="utf-8") as f:
        output = f.read()
        for key, value in config.flatten().items():
            output = output.replace(f"$px.{key}", value)

        for key, value in secrets.flatten().items():
            output = output.replace(f"$px.secrets.{key}", value)

    dest.parent.mkdir(exist_ok=True)
    with open(dest, "w", encoding="utf-8") as f:
        f.write(output)
