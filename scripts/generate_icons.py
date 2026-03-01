#!/usr/bin/env python3
"""
Generate PWA icon PNG files for Gizmo MY-AI.

Usage:
    pip install Pillow
    python scripts/generate_icons.py

Outputs:
    static/icons/icon-192.png
    static/icons/icon-512.png
"""

from pathlib import Path

ICONS_DIR = Path(__file__).resolve().parent.parent / "static" / "icons"
BG_COLOR = (108, 99, 255)   # #6C63FF — Gizmo purple
FG_COLOR = (255, 255, 255)  # white


def _make_icon(size: int, out_path: Path) -> None:
    from PIL import Image, ImageDraw, ImageFont

    img = Image.new("RGBA", (size, size), BG_COLOR + (255,))
    draw = ImageDraw.Draw(img)

    # Try to load a system font; fall back to default bitmap font
    font_size = int(size * 0.62)
    font = None
    for font_path in [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        "/Library/Fonts/Arial Bold.ttf",
        "C:/Windows/Fonts/arialbd.ttf",
    ]:
        try:
            font = ImageFont.truetype(font_path, font_size)
            break
        except (OSError, IOError):
            continue

    text = "G"
    if font:
        bbox = draw.textbbox((0, 0), text, font=font)
        text_w = bbox[2] - bbox[0]
        text_h = bbox[3] - bbox[1]
        x = (size - text_w) // 2 - bbox[0]
        y = (size - text_h) // 2 - bbox[1]
        draw.text((x, y), text, fill=FG_COLOR, font=font)
    else:
        # Default font fallback (small, but functional)
        draw.text((size // 2, size // 2), text, fill=FG_COLOR, anchor="mm")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(str(out_path), "PNG")
    print(f"  ✅  Saved {out_path}")


def main() -> None:
    print("Generating Gizmo PWA icons…")
    try:
        import PIL  # noqa: F401
    except ImportError:
        print("\n  ❌  Pillow is not installed.")
        print("Run `pip install Pillow` then re-run `python scripts/generate_icons.py`")
        raise SystemExit(1)

    _make_icon(192, ICONS_DIR / "icon-192.png")
    _make_icon(512, ICONS_DIR / "icon-512.png")
    print("Done.")


if __name__ == "__main__":
    main()
