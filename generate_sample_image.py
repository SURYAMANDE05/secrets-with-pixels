"""
generate_sample_image.py - Generates a sample cover image for testing
=====================================================================
Creates a colorful 640x480 test image with smooth gradient and geometric shapes.
"""

from PIL import Image, ImageDraw

def create_sample_cover(filename="sample_cover.png"):
    width, height = 640, 480
    img = Image.new("RGB", (width, height), color=(20, 24, 38))
    draw = ImageDraw.Draw(img)

    # Draw gradient background
    for y in range(height):
        r = int(20 + (y / height) * 80)
        g = int(30 + (y / height) * 40)
        b = int(70 + (y / height) * 120)
        draw.line([(0, y), (width, y)], fill=(r, g, b))

    # Draw decorative geometric elements
    draw.ellipse([80, 60, 240, 220], outline=(6, 182, 212), width=4)
    draw.rectangle([340, 100, 560, 320], outline=(16, 185, 129), width=3)
    draw.polygon([(160, 420), (280, 260), (400, 420)], outline=(245, 158, 11), width=3)

    img.save(filename, format="PNG")
    print(f"Created sample cover image: {filename} ({width}x{height} pixels, PNG format)")

if __name__ == "__main__":
    create_sample_cover()
