#!/usr/bin/env python3
"""
Instagram Graph API for Reels Publishing
Uploads video to Instagram Reels using official API
"""

import os
import requests
import json
from pathlib import Path

class InstagramPublisher:
    def __init__(self):
        self.access_token = os.getenv("INSTAGRAM_ACCESS_TOKEN")
        self.business_id = os.getenv("INSTAGRAM_BUSINESS_ID")
        
        if not all([self.access_token, self.business_id]):
            raise ValueError("Missing Instagram credentials in environment variables")
    
    def upload_video(self, video_path: str, caption: str) -> dict:
        """Upload video to Instagram Reels"""
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"Video file not found: {video_path}")
        
        # Step 1: Create container
        container_url = f"https://graph.facebook.com/v18.0/{self.business_id}/media"
        container_data = {
            "video_url": "",  # Need to upload video to accessible URL first
            "caption": caption,
            "media_type": "REELS"
        }
        
        # For direct upload, we need to use the video upload endpoint
        container_data = {
            "caption": caption,
            "media_type": "REELS",
            "video_url": ""  # Placeholder - will be replaced with actual upload
        }
        
        # Step 2: Upload video file (simplified version)
        # In production, you'd need to upload to a server first
        # For now, using direct upload approach
        
        upload_url = f"https://graph.facebook.com/v18.0/{self.business_id}/media"
        upload_data = {
            "caption": caption,
            "media_type": "REELS",
            "video_url": ""  # Need accessible URL
        }
        
        # Alternative: Direct file upload
        with open(video_path, "rb") as video_file:
            files = {"file": video_file}
            data = {
                "caption": caption,
                "access_token": self.access_token
            }
            upload_response = requests.post(
                f"https://graph.facebook.com/v18.0/{self.business_id}/media",
                files=files,
                data=data
            )
            upload_response.raise_for_status()
        
        upload_result = upload_response.json()
        container_id = upload_result.get("id")
        
        if not container_id:
            raise ValueError(f"Upload failed: {upload_result}")
        
        # Step 3: Publish the container
        publish_url = f"https://graph.facebook.com/v18.0/{self.business_id}/media_publish"
        publish_data = {
            "creation_id": container_id,
            "access_token": self.access_token
        }
        
        publish_response = requests.post(publish_url, json=publish_data)
        publish_response.raise_for_status()
        
        return publish_response.json()

def main():
    video_path = "output/video.mp4"
    caption_path = "output/instagram.txt"
    
    if not os.path.exists(caption_path):
        print("Error: Instagram caption file not found")
        return 1
    
    with open(caption_path, "r", encoding="utf-8") as f:
        caption = f.read().strip()
    
    try:
        publisher = InstagramPublisher()
        result = publisher.upload_video(video_path, caption)
        print(f"✅ Video uploaded to Instagram: {result}")
        return 0
    except Exception as e:
        print(f"❌ Failed to upload to Instagram: {e}")
        return 1

if __name__ == "__main__":
    exit(main())
