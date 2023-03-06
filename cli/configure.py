from pathlib import Path
from typing import Any
from .config import Config


def configure():
    secrets = Config(Path("secrets", "config.toml"))
    secrets.load()
    if not secrets.get(["ngrok", "auth_token"]):
        print(
            """Ngrok is used to test your setup locally. You can get a free account at ngrok.com
Please visit https://dashboard.ngrok.com/get-started/your-authtoken and paste in your auth token
        """
        )
        secrets.set(["ngrok", "auth_token"], input("What is your ngrok auth token? "))
        pass
    secrets.save()


def secrets_path():
    return Path("secrets", "config.toml")
