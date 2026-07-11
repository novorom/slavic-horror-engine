#!/usr/bin/env python3
"""
YouTube video uploader using OAuth refresh token.
"""

import os
import json
import logging
from pathlib import Path

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.auth.transport.requests import Request


class YouTubeUploader:
    def __init__(self, client_id: str, client_secret: str, refresh_token: str):
        self.client_id = client_id
        self.client_secret = client_secret
        self.refresh_token = refresh_token
        self.credentials = None
        self.youtube = None
        
    def authenticate(self):
        """Authenticate using refresh token."""
        self.credentials = Credentials(
            token=None,
            refresh_token=self.refresh_token,
            token_uri="https://oauth2.googleapis.com/token",
            client_id=self.client_id,
            client_secret=self.client_secret,
            scopes=["https://www.googleapis.com/auth/youtube.upload"]
        )
        
        # Refresh the token
        self.credentials.refresh(Request())
        
        # Build YouTube service
        self.youtube = build("youtube", "v3", credentials=self.credentials)
        
    def upload_video(
        self,
        video_path: str,
        title: str,
        description: str,
        tags: list[str] = None,
        category_id: str = "24",  # Entertainment
        privacy_status: str = "public"
    ) -> str:
        """Upload video to YouTube."""
        if not self.youtube:
            self.authenticate()
        
        body = {
            "snippet": {
                "title": title,
                "description": description,
                "tags": tags or [],
                "categoryId": category_id
            },
            "status": {
                "privacyStatus": privacy_status,
                "selfDeclaredMadeForKids": False
            }
        }
        
        media = MediaFileUpload(video_path, chunksize=-1, resumable=True)
        
        request = self.youtube.videos().insert(
            part="snippet,status",
            body=body,
            media_body=media
        )
        
        response = None
        while response is None:
            status, response = request.next_chunk()
            if status:
                logging.info(f"Uploaded {int(status.progress() * 100)}%")
        
        video_id = response["id"]
        logging.info(f"Video uploaded successfully! ID: {video_id}")
        return video_id


def main():
    import sys
    
    # Get credentials from environment
    client_id = os.getenv("YOUTUBE_CLIENT_ID")
    client_secret = os.getenv("YOUTUBE_CLIENT_SECRET")
    refresh_token = os.getenv("YOUTUBE_REFRESH_TOKEN")
    
    if not all([client_id, client_secret, refresh_token]):
        print("Error: Missing environment variables")
        print("Required: YOUTUBE_CLIENT_ID, YOUTUBE_CLIENT_SECRET, YOUTUBE_REFRESH_TOKEN")
        sys.exit(1)
    
    if len(sys.argv) < 2:
        print("Usage: python youtube_uploader.py <video_path> [title] [description]")
        sys.exit(1)
    
    video_path = sys.argv[1]
    title = sys.argv[2] if len(sys.argv) > 2 else "Horror Reel"
    description = sys.argv[3] if len(sys.argv) > 3 else ""
    
    if not Path(video_path).exists():
        print(f"Error: Video file not found: {video_path}")
        sys.exit(1)
    
    uploader = YouTubeUploader(client_id, client_secret, refresh_token)
    uploader.authenticate()
    
    video_id = uploader.upload_video(
        video_path=video_path,
        title=title,
        description=description,
        tags=["horror", "slavic", "folklore", "shorts", "terror"]
    )
    
    print(f"Video uploaded: https://www.youtube.com/watch?v={video_id}")


if __name__ == "__main__":
    main()
