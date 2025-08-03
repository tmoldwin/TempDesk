#!/usr/bin/env python3
"""
Create TempDesk icon - Desktop with Stopwatch Design
"""

from PIL import Image, ImageDraw, ImageFont
import os

def create_tempdesk_icon():
    """Create TempDesk icon with desktop and stopwatch design."""
    
    # Create base image (256x256 for high quality)
    size = 256
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Colors
    desktop_color = (45, 45, 45)  # Dark gray desktop
    monitor_color = (70, 70, 70)  # Slightly lighter monitor
    screen_color = (25, 25, 25)   # Dark screen
    stopwatch_color = (255, 255, 255)  # White stopwatch
    stopwatch_hands = (255, 100, 100)  # Red hands
    accent_color = (0, 120, 215)  # Blue accent
    
    # Draw desktop (bottom rectangle)
    desktop_width = int(size * 0.8)
    desktop_height = int(size * 0.15)
    desktop_x = (size - desktop_width) // 2
    desktop_y = size - desktop_height - 20
    
    draw.rectangle([desktop_x, desktop_y, desktop_x + desktop_width, desktop_y + desktop_height], 
                   fill=desktop_color, outline=(60, 60, 60), width=2)
    
    # Draw monitor (rectangle on desktop)
    monitor_width = int(size * 0.6)
    monitor_height = int(size * 0.4)
    monitor_x = (size - monitor_width) // 2
    monitor_y = desktop_y - monitor_height - 10
    
    # Monitor base
    draw.rectangle([monitor_x, monitor_y, monitor_x + monitor_width, monitor_y + monitor_height], 
                   fill=monitor_color, outline=(90, 90, 90), width=2)
    
    # Monitor screen
    screen_margin = 8
    screen_x = monitor_x + screen_margin
    screen_y = monitor_y + screen_margin
    screen_width = monitor_width - 2 * screen_margin
    screen_height = monitor_height - 2 * screen_margin
    
    draw.rectangle([screen_x, screen_y, screen_x + screen_width, screen_y + screen_height], 
                   fill=screen_color, outline=(50, 50, 50), width=1)
    
    # Draw stopwatch on the screen
    stopwatch_center_x = size // 2
    stopwatch_center_y = screen_y + screen_height // 2
    stopwatch_radius = int(size * 0.12)
    
    # Stopwatch outer circle
    draw.ellipse([stopwatch_center_x - stopwatch_radius, stopwatch_center_y - stopwatch_radius,
                   stopwatch_center_x + stopwatch_radius, stopwatch_center_y + stopwatch_radius],
                  fill=stopwatch_color, outline=(200, 200, 200), width=2)
    
    # Stopwatch inner circle
    inner_radius = int(stopwatch_radius * 0.8)
    draw.ellipse([stopwatch_center_x - inner_radius, stopwatch_center_y - inner_radius,
                   stopwatch_center_x + inner_radius, stopwatch_center_y + inner_radius],
                  fill=screen_color, outline=(100, 100, 100), width=1)
    
    # Stopwatch center dot
    center_dot_radius = 3
    draw.ellipse([stopwatch_center_x - center_dot_radius, stopwatch_center_y - center_dot_radius,
                   stopwatch_center_x + center_dot_radius, stopwatch_center_y + center_dot_radius],
                  fill=stopwatch_hands)
    
    # Stopwatch hands (hour and minute)
    import math
    
    # Hour hand (shorter, thicker)
    hour_angle = math.radians(45)  # 3 o'clock position
    hour_length = int(stopwatch_radius * 0.4)
    hour_end_x = stopwatch_center_x + int(hour_length * math.cos(hour_angle))
    hour_end_y = stopwatch_center_y - int(hour_length * math.sin(hour_angle))
    draw.line([stopwatch_center_x, stopwatch_center_y, hour_end_x, hour_end_y], 
              fill=stopwatch_hands, width=3)
    
    # Minute hand (longer, thinner)
    minute_angle = math.radians(270)  # 9 o'clock position
    minute_length = int(stopwatch_radius * 0.6)
    minute_end_x = stopwatch_center_x + int(minute_length * math.cos(minute_angle))
    minute_end_y = stopwatch_center_y - int(minute_length * math.sin(minute_angle))
    draw.line([stopwatch_center_x, stopwatch_center_y, minute_end_x, minute_end_y], 
              fill=stopwatch_hands, width=2)
    
    # Add some small details to the desktop
    # Keyboard (small rectangle)
    keyboard_width = int(desktop_width * 0.6)
    keyboard_height = int(desktop_height * 0.3)
    keyboard_x = desktop_x + (desktop_width - keyboard_width) // 2
    keyboard_y = desktop_y + desktop_height - keyboard_height - 5
    
    draw.rectangle([keyboard_x, keyboard_y, keyboard_x + keyboard_width, keyboard_y + keyboard_height],
                   fill=(55, 55, 55), outline=(80, 80, 80), width=1)
    
    # Add "TD" text in small letters on the desktop
    try:
        # Try to use a system font
        font = ImageFont.truetype("arial.ttf", 16)
    except:
        # Fallback to default font
        font = ImageFont.load_default()
    
    text = "TD"
    text_color = accent_color
    text_x = desktop_x + 10
    text_y = desktop_y + 5
    
    draw.text((text_x, text_y), text, fill=text_color, font=font)
    
    return img

def create_icons():
    """Create all icon sizes and save to icons folder."""
    
    # Ensure icons folder exists
    if not os.path.exists("icons"):
        os.makedirs("icons")
    
    # Create base icon
    icon = create_tempdesk_icon()
    
    # Save different sizes
    sizes = [16, 32, 48, 64, 128, 256]
    
    for size in sizes:
        resized_icon = icon.resize((size, size), Image.Resampling.LANCZOS)
        resized_icon.save(f"icons/tempdesk_icon_{size}.png", "PNG")
        print(f"Created icons/tempdesk_icon_{size}.png")
    
    # Create ICO file with multiple sizes
    icon_sizes = []
    for size in sizes:
        resized_icon = icon.resize((size, size), Image.Resampling.LANCZOS)
        icon_sizes.append(resized_icon)
    
    # Save ICO file in icons folder
    icon_sizes[0].save("icons/tempdesk_icon.ico", format='ICO', 
                       sizes=[(size, size) for size in sizes])
    print("Created icons/tempdesk_icon.ico")
    
    # Also save the main icon in root for backward compatibility
    icon.save("tempdesk_icon.ico", format='ICO', 
              sizes=[(size, size) for size in sizes])
    print("Created tempdesk_icon.ico (root directory)")

if __name__ == "__main__":
    create_icons()
    print("Icon creation complete!") 