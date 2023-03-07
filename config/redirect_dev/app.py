#! /usr/bin/env python
from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import urllib.request


class RedirectServer(BaseHTTPRequestHandler):
    def do_GET(self):
        with urllib.request.urlopen("http://ngrok:4040/api/tunnels") as response:
            redirect_url = json.load(response)["tunnels"][0]["public_url"]
            self.send_response(302)
            self.send_header("Location", redirect_url)
            self.end_headers()


if __name__ == "__main__":
    server = HTTPServer(("0.0.0.0", 8000), RedirectServer)

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
