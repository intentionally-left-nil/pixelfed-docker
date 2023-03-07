from pathlib import Path

from .service_config import ServiceConfig
from .config import Config


class NgrokConfig(ServiceConfig):
    @classmethod
    def configure(cls, secrets: Config):
        if not secrets.get(["ngrok", "auth_token"]):
            print(
                """Ngrok is used to test your setup locally. You can get a free account at ngrok.com
    Please visit https://dashboard.ngrok.com/get-started/your-authtoken and paste in your auth token
            """
            )
            secrets.set(
                ["ngrok", "auth_token"], input("What is your ngrok auth token? ")
            )

    @classmethod
    def update_files(cls, *, secrets: Config, template_dir: Path, secret_dir: Path):
        output = ""
        with open(template_dir.joinpath("ngrok.yml"), mode="r", encoding="utf-8") as f:
            output = f.read()
            for key, value in secrets.flatten().items():
                output = output.replace(f"${key}", value)
        (secret_dir / "ngrok").mkdir(exist_ok=True)
        with open(secret_dir / "ngrok" / "ngrok.yml", "w", encoding="utf-8") as f:
            f.write(output)
