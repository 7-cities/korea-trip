"""Generate PWA icons: 192, 512 (any), and 512-maskable.

Design: red rounded square background + white map-pin shape + small ㅋ glyph (Hangul giyeok-ieung, decorative).
The maskable version has a larger safe zone (icon contents stay within 80% radius).
"""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).parent
WEB = HERE.parent / "web"

RED = (211, 47, 47)         # #d32f2f — matches manifest theme_color
WHITE = (255, 255, 255)
NAVY = (33, 33, 48)


def draw_icon(size, maskable=False):
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)

    # Background: rounded square (or full bleed for maskable)
    radius = int(size * (0.2 if not maskable else 0.5))
    d.rounded_rectangle([(0, 0), (size, size)], radius=radius, fill=RED)

    # Safe-zone scale: maskable icons need contents inside an 80% center circle
    scale = 0.72 if maskable else 0.88
    cx, cy = size // 2, size // 2
    pin_w = int(size * scale * 0.55)
    pin_h = int(size * scale * 0.78)

    # Pin teardrop: circle + triangle
    top = cy - pin_h // 2
    circle_r = pin_w // 2
    circle_center_y = top + circle_r
    d.ellipse(
        [(cx - circle_r, circle_center_y - circle_r),
         (cx + circle_r, circle_center_y + circle_r)],
        fill=WHITE,
    )
    tri = [
        (cx - circle_r * 0.7, circle_center_y + circle_r * 0.55),
        (cx + circle_r * 0.7, circle_center_y + circle_r * 0.55),
        (cx, top + pin_h),
    ]
    d.polygon(tri, fill=WHITE)

    # Inner dot
    inner_r = int(circle_r * 0.38)
    d.ellipse(
        [(cx - inner_r, circle_center_y - inner_r),
         (cx + inner_r, circle_center_y + inner_r)],
        fill=RED,
    )

    return img


WEB.mkdir(exist_ok=True)
for size in (192, 512):
    img = draw_icon(size, maskable=False)
    img.save(WEB / f"icon-{size}.png", "PNG")
    print(f"  wrote icon-{size}.png")

img = draw_icon(512, maskable=True)
img.save(WEB / "icon-512-maskable.png", "PNG")
print("  wrote icon-512-maskable.png")

# Tiny SVG favicon
svg = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">
  <rect width="64" height="64" rx="12" fill="#d32f2f"/>
  <path d="M32 12c-7 0-12 5-12 12 0 8 12 24 12 24s12-16 12-24c0-7-5-12-12-12z" fill="#fff"/>
  <circle cx="32" cy="24" r="5" fill="#d32f2f"/>
</svg>
'''
(WEB / "favicon.svg").write_text(svg, encoding="utf-8")
print("  wrote favicon.svg")
