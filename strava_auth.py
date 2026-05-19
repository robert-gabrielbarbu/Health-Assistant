"""One-time OAuth flow to obtain and save a Strava refresh token."""

import os
import webbrowser
import urllib.parse
from http.server import BaseHTTPRequestHandler, HTTPServer
import requests
from dotenv import load_dotenv, set_key

load_dotenv()

CLIENT_ID = os.getenv("STRAVA_CLIENT_ID", "")
CLIENT_SECRET = os.getenv("STRAVA_CLIENT_SECRET", "")
REDIRECT_URI = "http://localhost:8765/callback"
ENV_FILE = os.path.join(os.path.dirname(__file__), ".env")

_auth_code: str = ""


class _CallbackHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        global _auth_code
        params = dict(urllib.parse.parse_qsl(urllib.parse.urlparse(self.path).query))
        _auth_code = params.get("code", "")
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"<h2>Authorization successful! You can close this tab.</h2>")

    def log_message(self, *_):
        pass


def main():
    if not CLIENT_ID or not CLIENT_SECRET:
        print("ERROR: STRAVA_CLIENT_ID and STRAVA_CLIENT_SECRET must be set in .env")
        return

    auth_url = (
        "https://www.strava.com/oauth/authorize"
        f"?client_id={CLIENT_ID}"
        "&response_type=code"
        f"&redirect_uri={urllib.parse.quote(REDIRECT_URI)}"
        "&approval_prompt=force"
        "&scope=read,activity:read_all"
    )

    print("Opening Strava authorization in your browser...")
    webbrowser.open(auth_url)

    server = HTTPServer(("localhost", 8765), _CallbackHandler)
    server.handle_request()

    if not _auth_code:
        print("ERROR: No authorization code received.")
        return

    resp = requests.post(
        "https://www.strava.com/oauth/token",
        data={
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "code": _auth_code,
            "grant_type": "authorization_code",
        },
        timeout=10,
    )
    resp.raise_for_status()
    data = resp.json()

    set_key(ENV_FILE, "STRAVA_REFRESH_TOKEN", data["refresh_token"])
    set_key(ENV_FILE, "STRAVA_ACCESS_TOKEN", data["access_token"])

    print("Tokens saved to .env — you're all set!")
    print(f"  Athlete: {data['athlete']['firstname']} {data['athlete']['lastname']}")


if __name__ == "__main__":
    main()
