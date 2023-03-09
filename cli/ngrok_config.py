from pathlib import Path

from .service_config import ServiceConfig
from .config import Config
from .dirs import Dirs
from .template import fill_template


class NgrokConfig(ServiceConfig):
    @classmethod
    def configure(cls, *, config: Config, secrets: Config):
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
    def update_files(cls, *, config: Config, secrets: Config, dirs: Dirs):
        fill_template(
            template=dirs.templates / "ngrok.yml",
            dest=dirs.secrets / "ngrok" / "ngrok.yml",
            config=config,
            secrets=secrets,
        )
