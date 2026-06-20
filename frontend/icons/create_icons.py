#!/usr/bin/env python3
"""Generate minimal PWA icons using Pillow."""
from PIL import Image, ImageDraw

def create_icon(size, filename):
    img = Image.new('RGBA', (size, size), (11, 15, 23, 255))  # dark navy background
    draw = ImageDraw.Draw(img)
    # Draw a shield shape (simple polygon)
    shield_color = (77, 168, 218, 255)  # #4da8da
    margin = size // 6
    draw.polygon([
        (size//2, margin),
        (size - margin, margin + size//5),
        (size - margin, size - margin),
        (size//2, size - margin//2),
        (margin, size - margin),
        (margin, margin + size//5)
    ], fill=shield_color)
    # White "E" letter
    from PIL import ImageFont
    try:
        font = ImageFont.truetype("arial.ttf", size//3)
    except:
        font = ImageFont.load_default()
    text = "E"
    # Use textbbox for centering
    bbox = draw.textbbox((0,0), text, font=font)
    w = bbox[2] - bbox[0]
    h = bbox[3] - bbox[1]
    draw.text(((size - w)/2, (size - h)/2 - size//30), text, fill="white", font=font)
    img.save(filename, "PNG")
    print(f"Created {filename}")

if __name__ == '__main__':
    create_icon(192, 'icon-192.png')
    create_icon(512, 'icon-512.png')
