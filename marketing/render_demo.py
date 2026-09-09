#!/usr/bin/env python3
"""Render the demo GIF for the README.

Every number and signature in FRAMES was produced by running this project's own
tools against org.jsoup:jsoup 1.17.2 and 1.23.2. Nothing here is illustrative.
Re-verify with marketing/capture_demo.py before changing any of it.

Usage:
    python3 -m venv /tmp/rvenv && /tmp/rvenv/bin/pip install pillow
    /tmp/rvenv/bin/python marketing/render_demo.py
"""

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

WIDTH = 880
PAD = 18
LINE_H = 21
FONT_SIZE = 15

BG = (13, 17, 23)
FG = (201, 209, 217)
DIM = (110, 118, 129)
GREEN = (63, 185, 80)
RED = (248, 81, 73)
YELLOW = (210, 153, 34)
BLUE = (88, 166, 255)

FONT_CANDIDATES = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
    "/usr/share/fonts/TTF/DejaVuSansMono.ttf",
    "/usr/share/fonts/dejavu/DejaVuSansMono.ttf",
    "/usr/share/fonts/liberation/LiberationMono-Regular.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationMono-Regular.ttf",
]


def load_font():
    for path in FONT_CANDIDATES:
        if Path(path).exists():
            return ImageFont.truetype(path, FONT_SIZE)
    return ImageFont.load_default()


# (text, color, hold_seconds_extra)
FRAMES = [
    [
        ("$ # Upgrading a dependency. Ask the agent what breaks.", DIM, 0.6),
    ],
    [
        ("$ # Upgrading a dependency. Ask the agent what breaks.", DIM, 0),
        ("", FG, 0),
        ("> I'm upgrading org.jsoup:jsoup from 1.17.2 to 1.23.2.", FG, 0),
        ("  What breaks?", FG, 1.2),
    ],
    [
        ("WITHOUT maven-decoder-mcp", RED, 0),
        ("", FG, 0),
        ("  jsoup 1.23.2 is largely backwards compatible with 1.17.2.", DIM, 0),
        ("  You should be fine, though you may want to check the", DIM, 0),
        ("  changelog for any deprecations.", DIM, 0),
        ("", FG, 0),
        ("  ^ Confident. Unsourced. It never opened the jar.", RED, 2.2),
    ],
    [
        ("WITH maven-decoder-mcp", GREEN, 0),
        ("", FG, 0),
        ("  -> compare_versions(org.jsoup:jsoup, 1.17.2, 1.23.2)", BLUE, 1.0),
    ],
    [
        ("WITH maven-decoder-mcp", GREEN, 0),
        ("", FG, 0),
        ("  -> compare_versions(org.jsoup:jsoup, 1.17.2, 1.23.2)", BLUE, 0),
        ("", FG, 0),
        ("     breaking_changes ......... 45", RED, 0),
        ("     members_removed .......... 31", RED, 0),
        ("     members_added ............ 150", GREEN, 0),
        ("     classes_with_api_changes . 47 of 115 compared", FG, 0),
        ("     compatible ............... false", RED, 2.6),
    ],
    [
        ("  Removed members, read from the bytecode:", FG, 0),
        ("", FG, 0),
        ("   org.jsoup.nodes.Document", DIM, 0),
        ("      - outerHtml()", RED, 0),
        ("      - updateMetaCharsetElement()", RED, 0),
        ("   org.jsoup.nodes.Element", DIM, 0),
        ("      - nextElementSibling()", RED, 0),
        ("      - previousElementSibling()", RED, 0),
        ("   org.jsoup.nodes.Node", DIM, 0),
        ("      - outerHtml(Appendable)", RED, 2.6),
    ],
    [
        ("  Members are compared AS DECLARED.", YELLOW, 0),
        ("  One that moved to a supertype is listed as removed and", DIM, 0),
        ("  may still be callable -- the tool says so in its output.", DIM, 0),
        ("", FG, 0),
        ("  You get the real diff, not a vibe.", FG, 2.4),
    ],
    [
        ("$ # No sources jar? Still works.", DIM, 0.8),
    ],
    [
        ("$ # No sources jar? Still works.", DIM, 0),
        ("", FG, 0),
        ("> What does org.jsoup.Jsoup actually expose?", FG, 0),
        ("", FG, 0),
        ("  -> extract_class_info  (falls back to javap)", BLUE, 1.2),
    ],
    [
        ("  public static Document parse(String)", FG, 0),
        ("  public static Document parse(String, String)", FG, 0),
        ("  public static Document parse(String, Parser)", FG, 0),
        ("  public static Document parse(File, String, String) throws IOException", FG, 0),
        ("  public static Connection connect(String)", FG, 0),
        ("  public static Connection newSession()", FG, 0),
        ("", FG, 0),
        ("  Straight out of the .class file. No sources jar required.", GREEN, 2.6),
    ],
    [
        ("Your agent guesses at library APIs it has never read.", FG, 0),
        ("This makes it read them.", GREEN, 0),
        ("", FG, 0),
        ("npx skills add https://github.com/salitaba/maven-decoder-mcp \\", BLUE, 0),
        ("     --skill maven-code-search", BLUE, 3.2),
    ],
]

FPS = 10
BASE_HOLD = 0.9


def render_frame(lines, font, height):
    img = Image.new("RGB", (WIDTH, height), BG)
    draw = ImageDraw.Draw(img)
    y = PAD
    for text, color, _ in lines:
        draw.text((PAD, y), text, font=font, fill=color)
        y += LINE_H
    return img


def main():
    font = load_font()
    max_lines = max(len(f) for f in FRAMES)
    height = PAD * 2 + LINE_H * max_lines

    images, durations = [], []
    for lines in FRAMES:
        img = render_frame(lines, font, height)
        hold = BASE_HOLD + max((h for _, _, h in lines), default=0)
        images.append(img)
        durations.append(int(hold * 1000))

    out = Path(__file__).resolve().parent.parent / "docs" / "demo.gif"
    out.parent.mkdir(parents=True, exist_ok=True)
    images[0].save(
        out,
        save_all=True,
        append_images=images[1:],
        duration=durations,
        loop=0,
        optimize=True,
    )
    size_kb = out.stat().st_size / 1024
    total_s = sum(durations) / 1000
    print(f"wrote {out}  {size_kb:.0f} KB  {total_s:.1f}s  {len(images)} frames  {WIDTH}x{height}")
    if size_kb > 5120:
        print("WARNING: over 5 MB, GitHub/Reddit will choke. Trim frames.")


if __name__ == "__main__":
    main()
