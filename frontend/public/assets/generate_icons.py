"""Generate Skarbol Tech brand icons for lead-gen web app."""
from PIL import Image, ImageDraw, ImageFont
import os, math

# Brand colors
DEEP_SPACE = (5, 10, 20)
NEURAL_BLUE = (10, 79, 217)
FUSION_CYAN = (0, 229, 255)
PHOTON_WHITE = (248, 250, 252)
STELLAR_VOID = (14, 24, 37)

def create_svg_favicon():
    """Create SVG favicon with Skarbol 'S' monogram."""
    svg = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">
  <defs>
    <linearGradient id="brand" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#0A4FD9"/>
      <stop offset="100%" stop-color="#00E5FF"/>
    </linearGradient>
  </defs>
  <rect width="64" height="64" rx="14" fill="#050A14"/>
  <rect x="3" y="3" width="58" height="58" rx="11" fill="none" stroke="url(#brand)" stroke-width="1.5" opacity="0.4"/>
  <text x="32" y="44" font-family="Inter, -apple-system, sans-serif" font-size="36" font-weight="800" fill="url(#brand)" text-anchor="middle" letter-spacing="-1">S</text>
</svg>'''
    return svg

def create_png_icon(size):
    """Create a PNG icon at given size with the Skarbol 'S' monogram."""
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Rounded square background
    margin = max(2, size // 16)
    bg_size = size - margin * 2
    radius = bg_size * 14 // 64
    draw.rounded_rectangle(
        [margin, margin, size - margin - 1, size - margin - 1],
        radius=radius, fill=DEEP_SPACE
    )

    # Inner border with gradient approximation (lighter blue)
    border = max(1, size // 32)
    inner_margin = margin + border
    inner_radius = max(1, radius - border)
    draw.rounded_rectangle(
        [inner_margin, inner_margin, size - inner_margin - 1, size - inner_margin - 1],
        radius=inner_radius, fill=None,
        outline=NEURAL_BLUE, width=border
    )

    # Draw 'S' using font or fallback to PIL drawing
    font_size = size * 22 // 32
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf", font_size)
    except:
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", font_size)
        except:
            font = ImageFont.load_default()

    # Get text bounding box
    bbox = draw.textbbox((0, 0), "S", font=font)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    tx = (size - tw) // 2 - bbox[0]
    ty = (size - th) // 2 - bbox[1] + (size // 12)  # slight vertical centering tweak

    # Draw with gradient effect (approximate with two passes)
    draw.text((tx, ty), "S", font=font, fill=FUSION_CYAN)
    draw.text((tx - 1, ty - 1), "S", font=font, fill=NEURAL_BLUE)

    # Bottom-right glow
    glow = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    gdraw = ImageDraw.Draw(glow)
    gdraw.ellipse(
        [size * 3 // 4, size * 3 // 4, size, size],
        fill=(0, 229, 255, 40)
    )
    img = Image.alpha_composite(img, glow)

    return img

outdir = os.path.dirname(os.path.abspath(__file__))

# SVG favicon
svg = create_svg_favicon()
with open(os.path.join(outdir, 'icon.svg'), 'w') as f:
    f.write(svg)
print("Created icon.svg")

# PNG sizes
for size in [16, 32, 48, 128, 192, 512]:
    img = create_png_icon(size)
    path = os.path.join(outdir, f'icon{size}.png')
    img.save(path, 'PNG')
    print(f"Created icon{size}.png")

# Also save as favicon.ico (use 32px as ico)
img32 = create_png_icon(32)
img32.save(os.path.join(outdir, 'favicon.ico'), 'ICO')
print("Created favicon.ico")

print("Done!")
