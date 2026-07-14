#!/usr/bin/env python3
"""
Social media publisher using BulkPublish API
Publishes videos to Instagram and TikTok automatically
"""

import os
import requests
import json
from pathlib import Path

# BulkPublish API
BULKPUBLISH_API_KEY = os.environ.get("BULKPUBLISH_API_KEY")
BULKPUBLISH_API_URL = "https://api.bulkpublish.com/api/posts"

# Cloudinary (for video hosting)
CLOUDINARY_CLOUD_NAME = os.environ.get("CLOUDINARY_CLOUD_NAME")
CLOUDINARY_API_KEY = os.environ.get("CLOUDINARY_API_KEY")
CLOUDINARY_API_SECRET = os.environ.get("CLOUDINARY_API_SECRET")


def upload_to_cloudinary(video_path: str) -> str:
    """
    Upload video to Cloudinary and return public URL
    
    Args:
        video_path: Path to video file
    
    Returns:
        Public URL of uploaded video
    """
    if not all([CLOUDINARY_CLOUD_NAME, CLOUDINARY_API_KEY, CLOUDINARY_API_SECRET]):
        print("ERROR: Cloudinary credentials not set")
        return None
    
    try:
        import cloudinary
        import cloudinary.uploader
        
        cloudinary.config(
            cloud_name=CLOUDINARY_CLOUD_NAME,
            api_key=CLOUDINARY_API_KEY,
            api_secret=CLOUDINARY_API_SECRET
        )
        
        # Upload video
        response = cloudinary.uploader.upload(
            video_path,
            resource_type="video",
            folder="horror_reels",
            public_id=f"reel_{Path(video_path).stem}"
        )
        
        return response.get("secure_url")
    except ImportError:
        print("ERROR: cloudinary package not installed. Run: pip install cloudinary")
        return None
    except Exception as e:
        print(f"ERROR: Failed to upload to Cloudinary: {e}")
        return None


def publish_to_social_media(video_url: str, caption: str, hashtags: list[str]) -> dict:
    """
    Publish video to Instagram and TikTok using BulkPublish API
    
    Args:
        video_url: Public URL of video
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
    
    # Only publish to TikTok (Instagram not connected yet)
    payload = {
        "platforms": ["tiktok"],
        "mediaUrl": video_url,
        "caption": full_caption,
        "postTypeOverrides": {
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
    
    # Read Instagram caption (use for TikTok too)
    instagram_file = output_dir / "instagram.txt"
    if instagram_file.exists():
        caption = instagram_file.read_text(encoding="utf-8").strip()
    else:
        print("ERROR: instagram.txt not found")
        exit(1)
    
    # Read hashtags
    hashtags_file = output_dir / "hashtags.txt"
    if hashtags_file.exists():
        hashtags = hashtags_file.read_text(encoding="utf-8").strip().split()
    else:
        hashtags = []
    
    # Video path
    video_path = str(output_dir / "video.mp4")
    
    if not Path(video_path).exists():
        print(f"ERROR: Video file not found: {video_path}")
        exit(1)
    
    # Upload to Cloudinary
    print("Uploading video to Cloudinary...")
    video_url = upload_to_cloudinary(video_path)
    
    if not video_url:
        print("ERROR: Failed to upload video to Cloudinary")
        exit(1)
    
    print(f"Video uploaded: {video_url}")
    
    # Publish to social media
    print("Publishing to TikTok...")
    result = publish_to_social_media(video_url, caption, hashtags)
    print(f"Publish result: {json.dumps(result, indent=2)}")
