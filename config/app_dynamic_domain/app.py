#! /usr/bin/env python

import urllib.request
from urllib.parse import urlparse
import json
import re


def get_domain():
    with urllib.request.urlopen("http://ngrok:4040/api/tunnels") as response:
        url = json.load(response)["tunnels"][0]["public_url"]
        return urlparse(url).hostname


if __name__ == "__main__":
    domain = get_domain()
    with open("/dev.env", "r", encoding="utf-8") as f:
        env = f.read()

        env = re.sub(
            r"^APP_URL=.*$", f"APP_URL=https://{domain}", env, flags=re.MULTILINE
        )
        env = re.sub(
            r"^APP_DOMAIN=.*$", f"APP_DOMAIN={domain}", env, flags=re.MULTILINE
        )
        env = re.sub(
            r"^ADMIN_DOMAIN=.*$", f"ADMIN_DOMAIN={domain}", env, flags=re.MULTILINE
        )
        env = re.sub(
            r"^SESSION_DOMAIN=.*$", f"SESSION_DOMAIN={domain}", env, flags=re.MULTILINE
        )

    with open("/dev.env", "w", encoding="utf-8") as f:
        f.write(env)
