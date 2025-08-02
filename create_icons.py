#!/usr/bin/env python3
"""
Icon generator for TempDrop
Creates basic colored rectangle icons for different file types.
"""

from PIL import Image, ImageDraw, ImageFont
import os

def create_icon(filename, color, text, size=(48, 48)):
    """Create a simple icon with color and text."""
    # Create image
    img = Image.new('RGBA', size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Draw colored rectangle
    draw.rectangle([2, 2, size[0]-2, size[1]-2], fill=color, outline=(255, 255, 255, 100), width=1)
    
    # Add text
    try:
        # Try to use a system font
        font = ImageFont.truetype("arial.ttf", 12)
    except:
        try:
            font = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", 12)
        except:
            font = ImageFont.load_default()
    
    # Center text
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    x = (size[0] - text_width) // 2
    y = (size[1] - text_height) // 2
    
    # Draw text with white color
    draw.text((x, y), text, fill=(255, 255, 255, 255), font=font)
    
    return img

def main():
    """Create all icons."""
    # Ensure icons directory exists
    os.makedirs("icons", exist_ok=True)
    
    # Define icons
    icons = [
        ("file.png", (100, 100, 100), "FILE"),
        ("pdf.png", (255, 0, 0), "PDF"),
        ("doc.png", (0, 0, 255), "DOC"),
        ("txt.png", (128, 128, 128), "TXT"),
        ("image.png", (0, 255, 0), "IMG"),
        ("video.png", (255, 0, 255), "VID"),
        ("audio.png", (255, 165, 0), "AUD"),
        ("archive.png", (128, 0, 128), "ZIP"),
    ]
    
    # Create icons
    for filename, color, text in icons:
        icon = create_icon(filename, color, text)
        icon.save(f"icons/{filename}")
        print(f"Created {filename}")
    
    print("All icons created successfully!")

if __name__ == "__main__":
    main() 