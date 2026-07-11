#!/usr/bin/env python3
"""
Generate YouTube channel assets: profile picture and banner.
"""

import requests
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import textwrap


def generate_profile_picture(output_path: Path = Path("channel_profile.jpg")):
    """Generate YouTube channel profile picture."""
    # Slavic horror themed profile picture
    prompt = "YouTube channel profile picture, slavic horror theme, mysterious dark forest with glowing eyes, ancient symbols, circular logo design, professional, high quality, dark atmosphere, horror aesthetic"
    
    url = f"https://image.pollinations.ai/prompt/{prompt}?width=800&height=800&seed=slavic_horror_profile&nologo=true"
    
    print(f"Generating profile picture...")
    response = requests.get(url)
    
    if response.status_code == 200:
        output_path.write_bytes(response.content)
        print(f"Profile picture saved: {output_path}")
        return output_path
    else:
        print(f"Error generating profile picture: {response.status_code}")
        return None


def generate_logo(output_path: Path = Path("channel_logo.jpg")):
    """Generate YouTube channel logo (square icon)."""
    # Simple, recognizable logo for channel branding
    prompt = "YouTube channel logo icon, simple minimalist design, slavic horror theme, dark forest with red eyes, ancient symbol, clean lines, recognizable at small size, professional, square format, horror aesthetic"
    
    url = f"https://image.pollinations.ai/prompt/{prompt}?width=500&height=500&seed=slavic_horror_logo_icon&nologo=true"
    
    print(f"Generating logo...")
    response = requests.get(url)
    
    if response.status_code == 200:
        output_path.write_bytes(response.content)
        print(f"Logo saved: {output_path}")
        return output_path
    else:
        print(f"Error generating logo: {response.status_code}")
        return None


def generate_banner(output_path: Path = Path("channel_banner.jpg")):
    """Generate YouTube channel banner (2560x1440)."""
    # Slavic horror themed banner
    prompt = "YouTube channel banner 2560x1440, slavic horror folklore theme, dark mysterious forest, ancient monsters lurking in shadows, Baba Yaga hut, glowing red eyes, atmospheric fog, horror movie aesthetic, professional quality, cinematic, dark moody colors"
    
    url = f"https://image.pollinations.ai/prompt/{prompt}?width=2560&height=1440&seed=slavic_horror_banner&nologo=true"
    
    print(f"Generating banner...")
    response = requests.get(url)
    
    if response.status_code == 200:
        output_path.write_bytes(response.content)
        print(f"Banner saved: {output_path}")
        
        # Add channel name text
        add_text_to_banner(output_path)
        return output_path
    else:
        print(f"Error generating banner: {response.status_code}")
        return None


def add_text_to_banner(image_path: Path):
    """Add channel name and tagline to banner within YouTube safe area."""
    try:
        img = Image.open(image_path)
        draw = ImageDraw.Draw(img)
        
        # YouTube safe area for text (center of banner)
        # Safe area: 1546x423 pixels in the center
        safe_width = 1546
        safe_height = 423
        safe_x = (img.width - safe_width) // 2
        safe_y = (img.height - safe_height) // 2
        
        # Try to use a nice font, fallback to default
        try:
            font_large = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 60)
            font_small = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 30)
        except:
            font_large = ImageFont.load_default()
            font_small = ImageFont.load_default()
        
        # Add channel name (shorter version)
        text = "Cuentos de Terror Eslavo"
        text_color = (255, 255, 255)  # White
        shadow_color = (0, 0, 0)  # Black shadow
        
        # Position for text (center of safe area)
        x = img.width // 2
        y = safe_y + safe_height // 2 - 30
        
        # Draw shadow
        bbox = draw.textbbox((0, 0), text, font=font_large)
        text_width = bbox[2] - bbox[0]
        text_x = x - text_width // 2
        
        draw.text((text_x + 2, y + 2), text, font=font_large, fill=shadow_color)
        draw.text((text_x, y), text, font=font_large, fill=text_color)
        
        # Add tagline
        tagline = "Leyendas oscuras del folklore eslavo"
        bbox_small = draw.textbbox((0, 0), tagline, font=font_small)
        tagline_width = bbox_small[2] - bbox_small[0]
        tagline_x = x - tagline_width // 2
        
        draw.text((tagline_x + 1, y + 65), tagline, font=font_small, fill=shadow_color)
        draw.text((tagline_x, y + 64), tagline, font=font_small, fill=(200, 200, 200))
        
        img.save(image_path)
        print(f"Text added to banner (within safe area)")
        
    except Exception as e:
        print(f"Error adding text to banner: {e}")


def main():
    output_dir = Path("channel_assets")
    output_dir.mkdir(exist_ok=True)
    
    profile_path = output_dir / "profile_picture.jpg"
    banner_path = output_dir / "banner.jpg"
    logo_path = output_dir / "logo.jpg"
    
    generate_profile_picture(profile_path)
    generate_banner(banner_path)
    generate_logo(logo_path)
    
    print(f"\nChannel assets generated in {output_dir}/")
    print(f"- Profile picture: {profile_path}")
    print(f"- Banner: {banner_path}")
    print(f"- Logo: {logo_path}")
    print(f"\nUpload these to YouTube Studio:")


if __name__ == "__main__":
    main()
