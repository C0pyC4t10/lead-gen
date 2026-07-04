"""Floodlit Monuments — stadium atmosphere canvas"""

from PIL import Image, ImageDraw, ImageFont, ImageFilter
import math, os

W, H = 1080, 1920

FONT_DIR = "/home/skarbolt/.config/opencode/skills/canvas-design/canvas-fonts"

def hex_to_rgb(h):
    h = h.lstrip('#')
    return tuple(int(h[i:i+2], 16) for i in (0,2,4))

def draw_beam(draw, x1, y1, x2, y2, color, width=40):
    """Draw a light beam with glowing edge"""
    for w in range(width, 0, -4):
        alpha = int(30 * (1 - w/width))
        c = (*color, alpha)
        draw.line([(x1, y1), (x2, y2)], fill=c, width=w)

def create_stadium_canvas():
    img = Image.new('RGBA', (W, H), (0, 0, 0, 255))
    draw = ImageDraw.Draw(img)

    # ── Background gradients ──
    # Deep night sky from top
    for y in range(H):
        t = y / H
        r = int(8 + 3 * (1-t))
        g = int(8 + 5 * (1-t))
        b = int(18 + 8 * (1-t))
        draw.point((0, y), fill=(r, g, b, 255))
        draw.point((1, y), fill=(r, g, b, 255))

    # Widen the gradient horizontally
    gradient = Image.new('RGBA', (W, H))
    gdraw = ImageDraw.Draw(gradient)
    for y in range(H):
        t = y / H
        r = int(8 + 6 * (1-t))
        g = int(8 + 8 * (1-t))
        b = int(18 + 12 * (1-t))
        gdraw.line([(0, y), (W, y)], fill=(r, g, b, 255))
    img = gradient

    draw = ImageDraw.Draw(img)

    # ── Stadium architecture — sweeping structural lines ──
    # Main arch (stadium roof curve)
    arch_pts = []
    for x in range(0, W, 4):
        t = x / W
        y = 200 + 400 * (t - 0.5)**2 * 4
        arch_pts.append((x, int(y)))
    for i in range(len(arch_pts)-1):
        x1, y1 = arch_pts[i]
        x2, y2 = arch_pts[i+1]
        draw.line([(x1, y1), (x2, y2)], fill=(35, 40, 55, 200), width=3)

    # Secondary inner arch
    arch2_pts = []
    for x in range(100, W-100, 3):
        t = (x-100) / (W-200)
        y = 280 + 320 * (t - 0.5)**2 * 4
        arch2_pts.append((x, int(y)))
    for i in range(len(arch2_pts)-1):
        x1, y1 = arch2_pts[i]
        x2, y2 = arch2_pts[i+1]
        draw.line([(x1, y1), (x2, y2)], fill=(50, 55, 75, 150), width=2)

    # Structural ribs (vertical/slanted lines from arch)
    for i in range(15):
        x = 80 + i * (W - 160) / 14
        t = i / 14
        arch_y = 200 + 400 * (t - 0.5)**2 * 4
        bottom_y = arch_y + 300 + (i % 3) * 40
        draw.line([(int(x), int(arch_y)), (int(x-20), int(bottom_y))],
                  fill=(40, 45, 65, 120), width=2)

    # ── Tiered stand patterns (silhouetted rows) ──
    for tier in range(6):
        base_y = 450 + tier * 65
        for row in range(20):
            ry = base_y + row * 8
            alpha = int(100 - tier * 12 - row * 3)
            if alpha < 20: alpha = 20
            x_offset = 60 + (tier * 10) + (row * 2)
            w_scale = 2 * (W - 2*x_offset)
            draw.rectangle(
                [x_offset + row*3, ry, W - x_offset - row*3, ry + 3],
                fill=(18, 20, 30, alpha)
            )

    # ── Floodlights ──
    light_sources = [
        (150, 100), (350, 80), (550, 70), (750, 80), (950, 100),
        (250, 60), (450, 55), (650, 55), (850, 60),
    ]

    for lx, ly in light_sources:
        # Light housing (small rectangle)
        draw.ellipse([lx-8, ly-6, lx+8, ly+6], fill=(180, 180, 200, 220))

        # Light beams spreading downward
        for angle_offset in range(-3, 4):
            angle = 85 + angle_offset * 5 + (lx/W) * 10
            rad = math.radians(angle)
            length = 500 + (angle_offset % 2) * 200
            ex = lx + math.cos(rad) * length
            ey = ly + math.sin(rad) * length
            beam_alpha = 15 - abs(angle_offset) * 3
            if beam_alpha > 0:
                draw.line([(lx, ly), (int(ex), int(ey))],
                          fill=(220, 220, 240, beam_alpha), width=6-abs(angle_offset))

    # ── Pitch glow at bottom ──
    pitch_rect = [80, 1550, W-80, 1850]
    # Green gradient on pitch
    for y in range(pitch_rect[1], pitch_rect[3], 2):
        t = (y - pitch_rect[1]) / (pitch_rect[3] - pitch_rect[1])
        g = int(25 + 30 * (1 - t))
        r = int(10 + 15 * (1 - t))
        b = int(15 + 20 * (1 - t))
        a = int(120 + 80 * t)
        draw.line([(pitch_rect[0], y), (pitch_rect[2], y)],
                  fill=(r, g, b, a), width=2)

    # Pitch glow upward
    for y in range(pitch_rect[1]-100, pitch_rect[1], 4):
        t = (pitch_rect[1] - y) / 100
        a = int(30 * (1-t))
        draw.line([(pitch_rect[0]+50, y), (pitch_rect[2]-50, y)],
                  fill=(20, 60, 30, a), width=2)

    # Pitch lines
    draw.rectangle(pitch_rect, outline=(60, 120, 70, 100), width=2)
    # Center line
    draw.line([(pitch_rect[0], (pitch_rect[1]+pitch_rect[3])//2),
               (pitch_rect[2], (pitch_rect[1]+pitch_rect[3])//2)],
              fill=(60, 120, 70, 80), width=1)
    # Center circle
    cx = (pitch_rect[0] + pitch_rect[2]) // 2
    cy = (pitch_rect[1] + pitch_rect[3]) // 2
    draw.ellipse([cx-60, cy-60, cx+60, cy+60], outline=(60, 120, 70, 60), width=2)

    # ── Goal frame silhouette ──
    goal_x = pitch_rect[0] + 30
    goal_top = pitch_rect[1] - 40
    # Post
    draw.line([(goal_x, goal_top), (goal_x, pitch_rect[3])],
              fill=(100, 100, 110, 120), width=5)
    draw.line([(goal_x, goal_top), (goal_x+120, goal_top)],
              fill=(100, 100, 110, 120), width=5)
    draw.line([(goal_x+120, goal_top), (goal_x+120, goal_top+80)],
              fill=(100, 100, 110, 100), width=4)
    # Net pattern
    for nx in range(goal_x+5, goal_x+115, 12):
        draw.line([(nx, goal_top+5), (nx, pitch_rect[3])],
                  fill=(60, 60, 70, 30), width=1)
    for ny in range(goal_top+10, pitch_rect[3], 15):
        draw.line([(goal_x+5, ny), (goal_x+115, ny)],
                  fill=(60, 60, 70, 25), width=1)

    return img


def add_text(img):
    draw = ImageDraw.Draw(img)
    W, H = img.size

    # Load fonts
    fonts_available = {}
    for fname in os.listdir(FONT_DIR):
        if fname.endswith('.ttf'):
            name = fname.replace('.ttf', '')
            fonts_available[name] = os.path.join(FONT_DIR, fname)

    # Try to load fonts, fall back to default
    font_team = None
    font_info = None
    font_small = None

    for name in ['Tektur-Regular', 'Tektur-Medium', 'Outfit-Bold', 'BigShoulders-Bold']:
        try:
            font_team = ImageFont.truetype(fonts_available[name], 140)
            break
        except:
            continue

    for name in ['PoiretOne-Regular', 'Outfit-Regular', 'WorkSans-Regular']:
        try:
            font_info = ImageFont.truetype(fonts_available[name], 42)
            break
        except:
            continue

    for name in ['DMMono-Regular', 'JetBrainsMono-Regular', 'RedHatMono-Regular']:
        try:
            font_small = ImageFont.truetype(fonts_available[name], 28)
            break
        except:
            continue

    if not font_team:
        font_team = ImageFont.load_default()
    if not font_info:
        font_info = ImageFont.load_default()
    if not font_small:
        font_small = ImageFont.load_default()

    # ── Text layout ──

    # "GER vs PAR" — big, centered
    team_text = "GER  vs  PAR"
    bbox = draw.textbbox((0, 0), team_text, font=font_team)
    tw = bbox[2] - bbox[0]
    tx = (W - tw) // 2
    ty = 1150
    # Glow behind text
    for glow_off, alpha in [(3, 40), (2, 60), (1, 80)]:
        draw.text((tx+glow_off, ty+glow_off), team_text,
                  fill=(255, 255, 255, alpha), font=font_team)
    draw.text((tx, ty), team_text, fill=(255, 255, 255, 230), font=font_team)

    # "ROUND OF 32" — above teams
    round_text = "ROUND OF 32"
    if font_info:
        bbox2 = draw.textbbox((0, 0), round_text, font=font_info)
        rw = bbox2[2] - bbox2[0]
        draw.text(((W - rw) // 2, ty - 65), round_text,
                  fill=(180, 180, 200, 160), font=font_info)

    # Date + venue line
    if font_small:
        meta_text = "BOSTON  •  29 JUNE 2026  •  KICKOFF 20:30"
        bbox3 = draw.textbbox((0, 0), meta_text, font=font_small)
        mw = bbox3[2] - bbox3[0]
        draw.text(((W - mw) // 2, ty + 170), meta_text,
                  fill=(160, 160, 180, 120), font=font_small)

    # FIFA World Cup badge-like accent
    accent_text = "FIFA WORLD CUP 2026™"
    if font_small:
        bbox4 = draw.textbbox((0, 0), accent_text, font=font_small)
        aw = bbox4[2] - bbox4[0]
        draw.text(((W - aw) // 2, ty - 115), accent_text,
                  fill=(200, 180, 100, 80), font=font_small)

    # Subtle corner mark — bottom right
    if font_small:
        corner = "sn  •  fc  •  bk"
        draw.text((W - 250, H - 60), corner,
                  fill=(100, 100, 120, 60), font=font_small)

    return img


def create_design_philosophy():
    return """# Floodlit Monuments

## A Design Philosophy

The stadium at night is the closest thing our century has to a cathedral. Sixty-five thousand souls gathered in a bowl of concrete and steel, floodlights burning away the darkness, the pitch glowing like an illuminated manuscript below. This philosophy treats the World Cup knockout match not as a sporting event but as a ritual gathering — ancient in its emotional architecture, modern in its material expression.

Space and form are dictated by the structural logic of the modern colosseum. Sweeping roof arches echo the curve of a held breath. Tiered stands rise in rhythmic repetition — not as detailed figures but as aggregate masses, humanity reduced to pattern and texture. The frame is architectural first, emotional second. The viewer exists within the structure, not outside it.

Light is the primary medium. Floodlight beams cut through darkness at precise angles, creating diagonal planes of visibility against deep shadow. This is not natural light — it is engineered illumination, purposeful and dramatic. The light source is always visible, always a reminder of the constructed nature of the spectacle. Warm white cutting through indigo night.

Color is restrained to a nearly monochromatic palette of deep navy, charcoal, and black, punctuated by the specific green of a floodlit pitch and the stark white of light beams. This is not a celebration of color but a study of contrast — the few vivid elements (pitch, floodlight, text) gaining power from the surrounding darkness.

Typography operates as an architectural element — not as information delivery but as structural accent. Large, condensed typefaces suggest scoreboard numerals and stadium signage. Small, precise labels float in the negative space like wayfinding systems. Text never explains; it anchors. The relationship between word and image is spatial, not narrative.

Composition follows the vertical logic of portrait format — from the vault of the roof through the mass of the stand down to the luminous field of play. The eye is guided downward by structural lines and light beams, arriving at the pitch as at an altar. Every element is meticulously positioned so the composition reads as a single, unified artifact — the product of countless refinements by someone at the absolute summit of their craft.

The work should feel like a film still from a documentary that does not exist — a single frame that contains an entire atmosphere. It is not about a specific match but about the condition of anticipation itself: the moment before anything happens, when everything is still possible, and sixty-five thousand people hold their breath together in a bowl of light and concrete.
"""


if __name__ == '__main__':
    os.makedirs('/home/skarbolt/kb/lead-gen/canvas_output', exist_ok=True)

    # Write philosophy
    philosophy = create_design_philosophy()
    with open('/home/skarbolt/kb/lead-gen/canvas_output/design_philosophy.md', 'w') as f:
        f.write(philosophy)

    # Create image
    img = create_stadium_canvas()
    img = add_text(img)

    out_path = '/home/skarbolt/kb/lead-gen/canvas_output/stadium_moment.png'
    img.save(out_path)
    print(f"Saved to {out_path}")
    print(f"Size: {img.size}")
