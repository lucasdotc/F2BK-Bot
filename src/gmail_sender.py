"""Send email through the Gmail API as f2bkagent@gmail.com.

One-time setup (run on a machine with a browser):
    python -m src.gmail_sender
It reads the OAuth client file (GMAIL_CREDENTIALS_FILE) and writes the token (GMAIL_TOKEN_FILE).
"""

import base64
import os
from email.message import EmailMessage

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/gmail.send"]  # send only: the bot can't read the inbox
CREDENTIALS_FILE = os.getenv("GMAIL_CREDENTIALS_FILE", "gmail_credentials.json")
TOKEN_FILE = os.getenv("GMAIL_TOKEN_FILE", "gmail_token.json")


def _credentials() -> Credentials:
    if not os.path.exists(TOKEN_FILE):
        raise RuntimeError(f"Gmail nao conectado: {TOKEN_FILE} nao existe. Rode `python -m src.gmail_sender`.")
    creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
    if not creds.valid:
        if creds.expired and creds.refresh_token:
            creds.refresh(Request())
            with open(TOKEN_FILE, "w") as f:
                f.write(creds.to_json())
        else:
            raise RuntimeError("Token do Gmail invalido. Rode `python -m src.gmail_sender` de novo.")
    return creds


def send_message(msg: EmailMessage) -> str:
    """Send one message; returns the Gmail message id."""
    service = build("gmail", "v1", credentials=_credentials(), cache_discovery=False)
    raw = base64.urlsafe_b64encode(bytes(msg)).decode()
    return service.users().messages().send(userId="me", body={"raw": raw}).execute()["id"]


if __name__ == "__main__":
    from google_auth_oauthlib.flow import InstalledAppFlow
    creds = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES).run_local_server(port=0)
    with open(TOKEN_FILE, "w") as f:
        f.write(creds.to_json())
    print(f"Gmail conectado. Token salvo em {TOKEN_FILE}")
