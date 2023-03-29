from pathlib import Path

from .config import Config


def fill_template(
    *,
    template: Path,
    dest: Path,
    config: Config,
    secrets: Config,
    overwrite_if_exists=True,
):
    output = ""
    with open(template, mode="r", encoding="utf-8") as f:
        output = f.read()
        for key, value in config.flatten().items():
            output = output.replace(f"${{px.{key}}}", value)

        for key, value in secrets.flatten().items():
            output = output.replace(f"${{px.secrets.{key}}}", value)

    dest.parent.mkdir(exist_ok=True, parents=True)
    mode = "w" if overwrite_if_exists else "x"
    try:
        with open(dest, mode, encoding="utf-8") as f:
            f.write(output)
    except FileExistsError as e:
        if overwrite_if_exists:
            raise e
