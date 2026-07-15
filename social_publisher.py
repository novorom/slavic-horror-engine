#!/usr/bin/env python3
"""
Social media publisher using SocialAPIs
Publishes videos to Instagram and TikTok automatically
"""

import os
import requests
import json
from pathlib import Path

# SocialAPIs
SOCIALAPIS_API_KEY = os.environ.get("SOCIALAPIS_API_KEY")
SOCIALAPIS_API_URL = "https://api.socialapis.io/v1/posts"

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


def publish_to_social_media(video_url: str, tiktok_caption: str, instagram_caption: str, hashtags: list[str]) -> dict:
    """
    Publish video to Instagram and TikTok using SocialAPIs
    
    Args:
        video_url: Public URL of video
        tiktok_caption: Caption for TikTok
        instagram_caption: Caption for Instagram
        hashtags: List of hashtags
    
    Returns:
        Response from SocialAPIs
    """
    if not SOCIALAPIS_API_KEY:
        print("ERROR: SOCIALAPIS_API_KEY not set")
        return {"error": "API key not set"}
    
    # Prepare captions with hashtags
    tiktok_full = f"{tiktok_caption}\n\n{' '.join(hashtags)}"
    instagram_full = f"{instagram_caption}\n\n{' '.join(hashtags)}"
    
    # Publish to TikTok only (Instagram not connected yet)
    payload = {
        "platforms": ["tiktok"],  # Add "instagram" when connected
        "media_url": video_url,
        "caption": tiktok_full,
        "post_type": "video"
    }
    
    headers = {
        "Authorization": f"Bearer {SOCIALAPIS_API_KEY}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.post(SOCIALAPIS_API_URL, json=payload, headers=headers)
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
    
    # Read TikTok caption
    tiktok_file = output_dir / "tiktok.txt"
    if tiktok_file.exists():
        tiktok_caption = tiktok_file.read_text(encoding="utf-8").strip()
    else:
        print("ERROR: tiktok.txt not found")
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
    result = publish_to_social_media(video_url, tiktok_caption, instagram_caption, hashtags)
    print(f"Publish result: {json.dumps(result, indent=2)}")
