#!/usr/bin/env python3
"""
Social media publisher using official TikTok and Instagram APIs
Publishes videos to Instagram and TikTok automatically
"""

import os
import requests
import json
from pathlib import Path

# TikTok Official API
TIKTOK_APP_KEY = os.environ.get("TIKTOK_APP_KEY")
TIKTOK_APP_SECRET = os.environ.get("TIKTOK_APP_SECRET")
TIKTOK_ACCESS_TOKEN = os.environ.get("TIKTOK_ACCESS_TOKEN")

# Instagram Graph API
INSTAGRAM_ACCESS_TOKEN = os.environ.get("INSTAGRAM_ACCESS_TOKEN")
INSTAGRAM_BUSINESS_ID = os.environ.get("INSTAGRAM_BUSINESS_ID")

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


def publish_to_tiktok(video_url: str, caption: str) -> dict:
    """
    Publish video to TikTok using official API
    
    Args:
        video_url: Public URL of video
        caption: Caption for the post
    
    Returns:
        Response from TikTok API
    """
    if not all([TIKTOK_APP_KEY, TIKTOK_APP_SECRET, TIKTOK_ACCESS_TOKEN]):
        print("ERROR: TikTok API credentials not set")
        return {"error": "API credentials not set"}
    
    # TikTok Content Posting API endpoint
    url = "https://open.tiktokapis.com/v2/video/upload/"
    
    payload = {
        "video_url": video_url,
        "caption": caption
    }
    
    headers = {
        "Authorization": f"Bearer {TIKTOK_ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"ERROR: Failed to publish to TikTok: {e}")
        return {"error": str(e)}


def publish_to_instagram(video_url: str, caption: str) -> dict:
    """
    Publish video to Instagram using Graph API
    
    Args:
        video_url: Public URL of video
        caption: Caption for the post
    
    Returns:
        Response from Instagram Graph API
    """
    if not all([INSTAGRAM_ACCESS_TOKEN, INSTAGRAM_BUSINESS_ID]):
        print("ERROR: Instagram API credentials not set")
        return {"error": "API credentials not set"}
    
    # Instagram Graph API endpoint for creating media container
    url = f"https://graph.facebook.com/v18.0/{INSTAGRAM_BUSINESS_ID}/media"
    
    payload = {
        "video_url": video_url,
        "caption": caption,
        "media_type": "REELS"
    }
    
    headers = {
        "Authorization": f"Bearer {INSTAGRAM_ACCESS_TOKEN}"
    }
    
    try:
        # Step 1: Create media container
        response = requests.post(url, data=payload, headers=headers)
        response.raise_for_status()
        container_id = response.json().get("id")
        
        # Step 2: Publish the container
        publish_url = f"https://graph.facebook.com/v18.0/{INSTAGRAM_BUSINESS_ID}/media_publish"
        publish_payload = {
            "creation_id": container_id
        }
        
        publish_response = requests.post(publish_url, data=publish_payload, headers=headers)
        publish_response.raise_for_status()
        
        return publish_response.json()
    except requests.exceptions.RequestException as e:
        print(f"ERROR: Failed to publish to Instagram: {e}")
        return {"error": str(e)}


def publish_to_social_media(video_url: str, tiktok_caption: str, instagram_caption: str, hashtags: list[str]) -> dict:
    """
    Publish video to Instagram and TikTok using official APIs
    
    Args:
        video_url: Public URL of video
        tiktok_caption: Caption for TikTok
        instagram_caption: Caption for Instagram
        hashtags: List of hashtags
    
    Returns:
        Combined response from both platforms
    """
    # Prepare captions with hashtags
    tiktok_full = f"{tiktok_caption}\n\n{' '.join(hashtags)}"
    instagram_full = f"{instagram_caption}\n\n{' '.join(hashtags)}"
    
    results = {}
    
    # Publish to TikTok
    print("Publishing to TikTok...")
    tiktok_result = publish_to_tiktok(video_url, tiktok_full)
    results["tiktok"] = tiktok_result
    
    # Publish to Instagram (only if credentials are set)
    if INSTAGRAM_ACCESS_TOKEN and INSTAGRAM_BUSINESS_ID:
        print("Publishing to Instagram...")
        instagram_result = publish_to_instagram(video_url, instagram_full)
        results["instagram"] = instagram_result
    else:
        print("Instagram credentials not set, skipping Instagram")
        results["instagram"] = {"status": "skipped", "reason": "credentials not set"}
    
    return results


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
