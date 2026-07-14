#!/usr/bin/env python3
"""
Social media publisher using BulkPublish API
Publishes videos to Instagram and TikTok automatically
"""

import os
import requests
import json
from pathlib import Path

BULKPUBLISH_API_KEY = os.environ.get("BULKPUBLISH_API_KEY")
BULKPUBLISH_API_URL = "https://api.bulkpublish.com/api/posts"


def publish_to_social_media(video_path: str, caption: str, hashtags: list[str]) -> dict:
    """
    Publish video to Instagram and TikTok using BulkPublish API
    
    Args:
        video_path: Path to video file
        caption: Caption for the post
        hashtags: List of hashtags
    
    Returns:
        Response from BulkPublish API
    """
    if not BULKPUBLISH_API_KEY:
        print("ERROR: BULKPUBLISH_API_KEY not set")
        return {"error": "API key not set"}
    
    # Prepare caption with hashtags
    full_caption = f"{caption}\n\n{' '.join(hashtags)}"
    
    # Upload video file (you may need to upload to a cloud storage first)
    # For now, we'll assume the video is accessible via URL
    # In production, you'd upload to S3, Cloudinary, or similar
    
    payload = {
        "platforms": ["instagram", "tiktok"],
        "mediaUrl": video_path,  # This should be a public URL
        "caption": full_caption,
        "postTypeOverrides": {
            "instagram": "reel",
            "tiktok": "video"
        }
    }
    
    headers = {
        "Authorization": f"Bearer {BULKPUBLISH_API_KEY}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.post(BULKPUBLISH_API_URL, json=payload, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"ERROR: Failed to publish: {e}")
        return {"error": str(e)}


if __name__ == "__main__":
    # Read metadata from generated files
    output_dir = Path("output")
    
    if not output_dir.exists():
        print("ERROR: output directory not found")
        exit(1)
    
    # Read Instagram caption
    instagram_file = output_dir / "instagram.txt"
    if instagram_file.exists():
        instagram_caption = instagram_file.read_text(encoding="utf-8").strip()
    else:
        print("ERROR: instagram.txt not found")
        exit(1)
    
    # Read hashtags
    hashtags_file = output_dir / "hashtags.txt"
    if hashtags_file.exists():
        hashtags = hashtags_file.read_text(encoding="utf-8").strip().split()
    else:
        hashtags = []
    
    # Video path (in production, this should be a public URL)
    video_path = str(output_dir / "video.mp4")
    
    # Note: BulkPublish requires a public URL for video
    # You need to upload the video to cloud storage first (S3, Cloudinary, etc.)
    # For now, this is a placeholder
    print("WARNING: Video needs to be uploaded to cloud storage first")
    print(f"Video path: {video_path}")
    print(f"Caption: {instagram_caption}")
    print(f"Hashtags: {hashtags}")
    
    # Uncomment when video is hosted:
    # result = publish_to_social_media(video_path, instagram_caption, hashtags)
    # print(f"Publish result: {json.dumps(result, indent=2)}")
