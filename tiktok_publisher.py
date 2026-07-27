#!/usr/bin/env python3
"""
TikTok Content Publishing API
Uploads video to TikTok using official API
"""

import os
import requests
import json
from pathlib import Path

class TikTokPublisher:
    def __init__(self):
        self.client_id = os.getenv("TIKTOK_CLIENT_ID")
        self.client_secret = os.getenv("TIKTOK_CLIENT_SECRET")
        self.access_token = os.getenv("TIKTOK_ACCESS_TOKEN")
        
        if not all([self.client_id, self.client_secret, self.access_token]):
            raise ValueError("Missing TikTok credentials in environment variables")
    
    def upload_video(self, video_path: str, caption: str) -> dict:
        """Upload video to TikTok"""
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"Video file not found: {video_path}")
        
        # Step 1: Initialize upload
        init_url = "https://open.tiktokapis.com/v2/video/upload/"
        init_headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        init_data = {
            "video": {
                "file_size": os.path.getsize(video_path)
            }
        }
        
        init_response = requests.post(init_url, headers=init_headers, json=init_data)
        init_response.raise_for_status()
        upload_data = init_response.json()
        
        # Step 2: Upload video file
        upload_url = upload_data["data"]["upload_url"]
        video_id = upload_data["data"]["video_id"]
        
        with open(video_path, "rb") as video_file:
            upload_response = requests.put(upload_url, data=video_file)
            upload_response.raise_for_status()
        
        # Step 3: Publish video
        publish_url = "https://open.tiktokapis.com/v2/video/publish/"
        publish_headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        publish_data = {
            "video": {
                "video_id": video_id,
                "caption": caption
            }
        }
        
        publish_response = requests.post(publish_url, headers=publish_headers, json=publish_data)
        publish_response.raise_for_status()
        
        return publish_response.json()

def main():
    video_path = "output/video.mp4"
    caption_path = "output/tiktok.txt"
    
    if not os.path.exists(caption_path):
        print("Error: TikTok caption file not found")
        return 1
    
    with open(caption_path, "r", encoding="utf-8") as f:
        caption = f.read().strip()
    
    try:
        publisher = TikTokPublisher()
        result = publisher.upload_video(video_path, caption)
        print(f"✅ Video uploaded to TikTok: {result}")
        return 0
    except Exception as e:
        print(f"❌ Failed to upload to TikTok: {e}")
        return 1

if __name__ == "__main__":
    exit(main())
