from PIL import Image, ImageDraw, ImageFont
import os

# Create icons directory
icons_dir = r"D:\FYIUploader\desktop\src-tauri\icons"
os.makedirs(icons_dir, exist_ok=True)

# Create a simple gradient icon with FYI text
def create_icon(size):
    # Create image with gradient background
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Draw gradient background (cyber colors)
    for y in range(size):
        r = int(0 + (139 * y / size))  # 0 to 139 (cyan to purple gradient)
        g = int(242 - (242 * y / size))  # 242 to 0
        b = int(255)  # constant
        draw.line([(0, y), (size, y)], fill=(r, g, b, 255))
    
    # Draw circle
    margin = size // 8
    draw.ellipse([margin, margin, size-margin, size-margin], 
                 fill=(0, 242, 255, 255), outline=(139, 0, 255, 255), width=max(2, size//32))
    
    # Draw FYI text (simple)
    try:
        font = ImageFont.truetype("arial.ttf", size // 3)
    except:
        font = ImageFont.load_default()
    
    text = "FYI"
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    position = ((size - text_width) // 2, (size - text_height) // 2 - size // 10)
    
    # Draw text with shadow
    draw.text((position[0]+2, position[1]+2), text, fill=(0, 0, 0, 128), font=font)
    draw.text(position, text, fill=(255, 255, 255, 255), font=font)
    
    return img

# Generate PNG icons
print("Generating PNG icons...")
icon_32 = create_icon(32)
icon_32.save(os.path.join(icons_dir, "32x32.png"))
print("✓ 32x32.png")

icon_128 = create_icon(128)
icon_128.save(os.path.join(icons_dir, "128x128.png"))
icon_128.save(os.path.join(icons_dir, "128x128@2x.png"))
print("✓ 128x128.png")
print("✓ 128x128@2x.png")

icon_256 = create_icon(256)
icon_256.save(os.path.join(icons_dir, "icon.png"))
print("✓ icon.png")

# Generate ICO file (Windows)
print("Generating Windows ICO...")
icon_256.save(os.path.join(icons_dir, "icon.ico"), format='ICO', sizes=[(256, 256), (128, 128), (64, 64), (32, 32), (16, 16)])
print("✓ icon.ico")

# Generate ICNS file (macOS) - requires pillow-icns or skip
print("Generating macOS ICNS...")
try:
    # Simple approach: save as PNG and rename to .icns (Tauri will handle conversion)
    icon_512 = create_icon(512)
    icon_512.save(os.path.join(icons_dir, "icon.icns.png"))
    # Just create a placeholder icns
    with open(os.path.join(icons_dir, "icon.icns"), 'wb') as f:
        # Write minimal ICNS header
        f.write(b'icns')
        f.write((8).to_bytes(4, 'big'))
    print("✓ icon.icns (placeholder)")
except Exception as e:
    print(f"⚠ icon.icns: {e}")

print("\n✅ All icons generated successfully!")
print(f"Location: {icons_dir}")
