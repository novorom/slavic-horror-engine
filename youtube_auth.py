#!/usr/bin/env python3
"""
Script to get YouTube OAuth refresh token.
Run this locally once to authorize and get refresh token.
"""

import json
import webbrowser
from pathlib import Path
from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.parse

# Install required: pip install google-auth-oauthlib google-auth-httplib2 google-api-python-client
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]


def get_refresh_token(credentials_path: str) -> str:
    """Get refresh token from OAuth credentials."""
    flow = InstalledAppFlow.from_client_secrets_file(credentials_path, SCOPES)
    
    # Run local server for callback (try different ports)
    for port in [8080, 8081, 8082, 8083, 8084]:
        try:
            credentials = flow.run_local_server(
                port=port,
                prompt="consent",
                authorization_prompt_message="Please visit this URL to authorize this application: {url}",
                success_message="Authorization successful! You can close this window.",
            )
            return credentials.refresh_token
        except OSError as e:
            if "Address already in use" in str(e):
                continue
            raise
    raise Exception("Could not find available port for OAuth callback")


def main():
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python youtube_auth.py <path_to_credentials.json>")
        print("Example: python youtube_auth.py ~/Downloads/client_secret_XXX.json")
        sys.exit(1)
    
    credentials_path = sys.argv[1]
    credentials_file = Path(credentials_path)
    
    if not credentials_file.exists():
        print(f"Error: Credentials file not found: {credentials_path}")
        sys.exit(1)
    
    print("Opening browser for authorization...")
    print(f"Using credentials from: {credentials_path}")
    
    try:
        refresh_token = get_refresh_token(str(credentials_file))
        print("\n" + "="*60)
        print("SUCCESS! Your refresh token:")
        print("="*60)
        print(refresh_token)
        print("="*60)
        print("\nAdd this to GitHub Secrets as YOUTUBE_REFRESH_TOKEN")
        print("Also add from your credentials.json:")
        print("  - client_id as YOUTUBE_CLIENT_ID")
        print("  - client_secret as YOUTUBE_CLIENT_SECRET")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
