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
