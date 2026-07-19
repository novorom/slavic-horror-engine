#!/usr/bin/env python3
"""
Telegram bot for sending video and descriptions to user
Sends generated video, TikTok description, Instagram description, and hashtags
"""

import os
import requests
from pathlib import Path

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")


def send_telegram_message(text: str) -> bool:
    """
    Send text message via Telegram bot
    
    Args:
        text: Message text
    
    Returns:
        True if successful, False otherwise
    """
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("ERROR: Telegram bot token or chat ID not set")
        return False
    
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": text,
        "parse_mode": "HTML"
    }
    
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        return True
    except requests.exceptions.RequestException as e:
        print(f"ERROR: Failed to send Telegram message: {e}")
        return False


def send_telegram_video(video_path: str, caption: str) -> bool:
    """
    Send video via Telegram bot
    
    Args:
        video_path: Path to video file
        caption: Video caption
    
    Returns:
        True if successful, False otherwise
    """
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("ERROR: Telegram bot token or chat ID not set")
        return False
    
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendVideo"
    
    try:
        with open(video_path, 'rb') as video_file:
            payload = {
                "chat_id": TELEGRAM_CHAT_ID,
                "caption": caption,
                "parse_mode": "HTML"
            }
            files = {
                "video": video_file
            }
            response = requests.post(url, data=payload, files=files)
            response.raise_for_status()
            return True
    except requests.exceptions.RequestException as e:
        print(f"ERROR: Failed to send Telegram video: {e}")
        return False


if __name__ == "__main__":
    output_dir = Path("output")
    
    if not output_dir.exists():
        print("ERROR: output directory not found")
        exit(1)
    
    # Read TikTok description
    tiktok_file = output_dir / "tiktok.txt"
    if tiktok_file.exists():
        tiktok_caption = tiktok_file.read_text(encoding="utf-8").strip()
    else:
        print("ERROR: tiktok.txt not found")
        exit(1)
    
    # Read Instagram description
    instagram_file = output_dir / "instagram.txt"
    if instagram_file.exists():
        instagram_caption = instagram_file.read_text(encoding="utf-8").strip()
    else:
        print("ERROR: instagram.txt not found")
        exit(1)
    
    # Read hashtags
    hashtags_file = output_dir / "hashtags.txt"
    if hashtags_file.exists():
        hashtags = hashtags_file.read_text(encoding="utf-8").strip()
    else:
        hashtags = ""
    
    # Video path
    video_path = output_dir / "video.mp4"
    
    if not video_path.exists():
        print(f"ERROR: Video file not found: {video_path}")
        exit(1)
    
    # Send video
    print("Sending video to Telegram...")
    video_caption = f"<b>🎬 New Horror Reel</b>\n\n<b>TikTok:</b>\n{tiktok_caption}\n\n<b>Instagram:</b>\n{instagram_caption}\n\n<b>Hashtags:</b>\n{hashtags}"
    
    if send_telegram_video(str(video_path), video_caption):
        print("Video sent successfully!")
    else:
        print("Failed to send video")
        exit(1)
