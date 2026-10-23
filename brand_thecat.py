#!/usr/bin/env python3
"""Brand official TDesktop as TheCat (en) / کت (fa).

- logos: Resources/art/icon* + logo* ← logo.png in the repo root
- links: telegram.org → catroom.ir, t.me → cr0.ir
- names: output_name TheCat, bundle ir.catroom.thecat, fa.lproj display name کت

Paths resolve relative to this script, so the same script works on a local
checkout and on a CI runner:
    python brand_thecat.py [--tdesktop PATH]
"""
from __future__ import annotations

import argparse
import pathlib
import shutil
import sys

ROOT = pathlib.Path(__file__).resolve().parent

# Windows consoles default to a legacy code page that cannot encode "→" or the
# Persian strings below; never let a print statement fail the build.
for stream in (sys.stdout, sys.stderr):
    try:
        stream.reconfigure(errors="replace")
    except (AttributeError, ValueError):
        pass


def die(msg: str) -> None:
    print("ERROR:", msg, file=sys.stderr)
    sys.exit(1)


def replace_logos(src: pathlib.Path, logo: pathlib.Path) -> None:
    art = src / "Telegram/Resources/art"
    if not logo.is_file():
        die(f"missing logo {logo}")
    targets = []
    for path in art.rglob("*"):
        if not path.is_file():
            continue
        name = path.name.lower()
        if name.startswith("icon") and name.endswith((".png", ".ico")):
            targets.append(path)
        elif name.startswith("logo") and name.endswith(".png"):
            targets.append(path)
    if not targets:
        die("no icon/logo targets under Resources/art")
    for path in targets:
        if path.suffix == ".ico":
            # .ico needs a real ICO container; keep the upstream one.
            print(f"  skip ico {path.name}")
            continue
        try:
            resize_with_pillow(logo, path)
            print(f"  logo → {path.relative_to(src)}")
        except Exception as e:  # noqa: BLE001
            print(f"  FAILED {path}: {e}")
            raise


def replace_app_icon(src: pathlib.Path, logo: pathlib.Path) -> None:
    """Fill the macOS asset catalog — that is what the Dock/Finder icon uses.

    Resources/art/icon*.png are in-app images; the .app bundle icon comes from
    Images.xcassets/Icon.appiconset (compiled to Assets.car + Icon.icns), so
    branding art alone leaves the Telegram logo in the Dock.
    """
    appiconset = src / "Telegram/Telegram/Images.xcassets/Icon.appiconset"
    if not appiconset.is_dir():
        die(f"missing {appiconset}")
    done = 0
    for name in ("Icon.appiconset", "Icon.iconset"):
        folder = src / "Telegram/Telegram/Images.xcassets" / name
        if not folder.is_dir():
            continue
        for path in sorted(folder.glob("*.png")):
            resize_square(logo, path)
            done += 1
    print(f"  app icon → {done} files in Icon.appiconset/Icon.iconset")


def make_tray_icons(src: pathlib.Path, logo: pathlib.Path) -> None:
    """macOS menu bar draws a template image from Resources/icons.

    tray_mac.mm paints the asset in windowFg, so it is tinted with the app
    foreground colour and drawn from its alpha — a photo dropped in here would
    become a solid block. Only the mark itself may be inked.
    """
    icons = src / "Telegram/Resources/icons"
    for suffix, size in (("", 22), ("@2x", 44), ("@3x", 66)):
        target = icons / f"mac_tray_icon{suffix}.png"
        if not target.is_file():
            print(f"  WARNING: missing {target.name}")
            continue
        write_template_icon(logo, target, size)
        print(f"  tray → {target.relative_to(src)}")


def write_template_icon(logo: pathlib.Path, target: pathlib.Path,
                        size: int) -> None:
    """Render the logo's mark as a black silhouette over transparency.

    The art is a cyan card with a white inner panel, and the mark is the cyan
    glyph inside that panel. The card and the mark share a colour, so neither
    luminance nor chroma separates them — only position does. The panel is
    located first (the bright region), then everything inside it that is not
    panel-white becomes ink, and the whole thing is cropped to the mark so it
    fills the menu-bar slot instead of floating in a square of padding.
    """
    from PIL import Image, ImageFilter

    with Image.open(logo) as source:
        img = source.convert("RGBA")

    # Work at a fixed working size so thresholds are resolution-independent.
    work = img.resize((256, 256), Image.LANCZOS)
    ink = mark_mask(work)
    box = ink.getbbox()
    if box is None:
        die(f"{logo} produced an empty tray silhouette")

    # Square the box around its centre so the glyph keeps its proportions.
    cx, cy = (box[0] + box[2]) / 2, (box[1] + box[3]) / 2
    half = max(box[2] - box[0], box[3] - box[1]) / 2
    pad = max(4, int(half * 0.12))
    half += pad
    square = (
        max(0, int(cx - half)), max(0, int(cy - half)),
        min(256, int(cx + half) + 1), min(256, int(cy + half) + 1),
    )
    # macOS menu-bar glyphs keep a margin inside their slot; a mark that fills
    # the tile edge-to-edge reads as a blob next to system icons.
    inner = max(int(size * 0.78), 1)
    mask = ink.crop(square).resize((inner, inner), Image.LANCZOS)
    out = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    offset = (size - inner) // 2
    # Paste the mask as the alpha channel, not as an opaque grey image:
    # paste() with an "L" source writes it into every band.
    canvas = Image.new("L", (size, size), 0)
    canvas.paste(mask, (offset, offset))
    out.putalpha(canvas)
    out.save(target)


def mark_mask(work) -> "Image.Image":
    """Alpha isolating the paw glyph at the working resolution.

    The art nests four shapes: a cyan card, a white rounded panel on it, a
    white cross on the panel, and the paw knocked out of the cross in the same
    cyan as the card. The card and the paw share a colour, so the only thing
    that tells them apart is reachability: card-cyan is joined to the image
    border, the paw is not. Take the cyan that the border cannot reach.
    """
    from PIL import Image, ImageFilter

    w, h = work.size
    px = work.load()

    def cyan(x, y):
        r, g, b, a = px[x, y]
        if a <= 128:
            return False
        chroma = max(r, g, b) - min(r, g, b)
        lum = (r * 299 + g * 587 + b * 114) // 1000
        return chroma > 45 and lum < 215

    # Everything, not just cyan, for the flood, so white cannot be crossed.
    def passable(x, y):
        r, g, b, a = px[x, y]
        return a > 128 and (r * 299 + g * 587 + b * 114) // 1000 <= 205

    seen = [[False] * w for _ in range(h)]
    stack = [(x, y) for x in range(w) for y in (0, h - 1) if passable(x, y)]
    stack += [(x, y) for y in range(h) for x in (0, w - 1) if passable(x, y)]
    for x, y in stack:
        seen[y][x] = True
    while stack:
        x, y = stack.pop()
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nx, ny = x + dx, y + dy
            if 0 <= nx < w and 0 <= ny < h and not seen[ny][nx] and passable(nx, ny):
                seen[ny][nx] = True
                stack.append((nx, ny))

    candidates = [
        (x, y)
        for y in range(h)
        for x in range(w)
        if cyan(x, y) and not seen[y][x]
    ]
    # The unreachable cyan also includes the cross's four arms, which are
    # enclosed by the panel in the same way. The paw is the one blob near the
    # centre of the image; keep only that connected component.
    keep = central_component(candidates, w, h)

    mask = Image.new("L", (w, h))
    mpx = mask.load()
    for x, y in keep:
        mpx[x, y] = 255
    return mask.filter(ImageFilter.GaussianBlur(0.6))


def central_component(points, w, h):
    """The connected component of `points` whose centroid is nearest centre."""
    remaining = set(points)
    best, best_dist = set(), None
    cx0, cy0 = w / 2, h / 2
    while remaining:
        seed = remaining.pop()
        comp = [seed]
        stack = [seed]
        while stack:
            x, y = stack.pop()
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1),
                           (1, 1), (1, -1), (-1, 1), (-1, -1)):
                n = (x + dx, y + dy)
                if n in remaining:
                    remaining.discard(n)
                    comp.append(n)
                    stack.append(n)
        mx = sum(p[0] for p in comp) / len(comp)
        my = sum(p[1] for p in comp) / len(comp)
        dist = (mx - cx0) ** 2 + (my - cy0) ** 2
        if best_dist is None or dist < best_dist:
            best, best_dist = set(comp), dist
    return best


def find_bright_panel(img) -> tuple[int, int, int, int] | None:
    """Bounding box of the light inner panel of the logo card."""
    w, h = img.size
    px = img.load()
    xs, ys = [], []
    for y in range(0, h, 2):
        for x in range(0, w, 2):
            r, g, b, a = px[x, y]
            if a > 200 and r > 235 and g > 235 and b > 235:
                xs.append(x)
                ys.append(y)
    if len(xs) < (w * h) // 200:
        return None
    return (min(xs), min(ys), max(xs) + 1, max(ys) + 1)


def resize_square(logo: pathlib.Path, target: pathlib.Path) -> None:
    """Scale the logo to a square of the target's size, keeping transparency."""
    from PIL import Image
    w, h = Image.open(target).size
    with Image.open(logo) as source:
        source.convert("RGBA").resize((w, h), Image.LANCZOS).save(target)


def resize_with_pillow(logo: pathlib.Path, target: pathlib.Path) -> None:
    try:
        from PIL import Image
    except ImportError:
        die("Pillow is required to resize icons off macOS: pip install pillow")
    with Image.open(target) as current:
        size = current.size
    with Image.open(logo) as source:
        source.convert("RGBA").resize(size, Image.LANCZOS).save(target)


def require_pillow() -> None:
    try:
        from PIL import Image  # noqa: F401
    except ImportError:
        die("Pillow is required to resize icons off macOS: pip install pillow")


TEXT_EXTS = {
    ".cpp", ".h", ".mm", ".m", ".pl", ".py", ".json", ".md", ".txt",
    ".cmake", ".html", ".js", ".css", ".strings",
}

# Order matters: longer, more specific pairs must come before the bare domain
# ones, or "https://core.telegram.org/api" would become
# "https://core.catroom.ir/api" instead of the API site.
LINK_PAIRS = [
    # API documentation and the project itself.
    ("https://core.telegram.org/api", "https://catroom.ir/thecat-api"),
    ("https://core.telegram.org/", "https://catroom.ir/thecat-api/"),
    ("https://core.telegram.org", "https://catroom.ir/thecat-api"),
    ("https://github.com/telegramdesktop/tdesktop", "https://github.com/mrfelfel/thecat-desktop-build"),
    # t.me links are served by the Cat's own short-link host.
    ("https://t.me/", "https://cr0.ir/"),
    ("http://t.me/", "http://cr0.ir/"),
    ("//t.me/", "//cr0.ir/"),
    # Bare host in prose: "Public links such as t.me/title".
    ("t.me/", "cr0.ir/"),
    ("**t.me/**", "**cr0.ir/**"),
    # TheCat has no Fragment; its marketplace is Kat Market.
    ("https://fragment.com/ads/topup", "https://catroom.ir/katmarket/topup"),
    ("https://fragment.com/", "https://catroom.ir/katmarket/"),
    ("https://fragment.com", "https://catroom.ir/katmarket"),
    ("//fragment.com/", "//catroom.ir/katmarket/"),
    ("//fragment.com", "//catroom.ir/katmarket"),
    # Remaining telegram hosts.
    ("https://ads.telegram.org", "https://ads.catroom.ir"),
    ("https://telegram.org", "https://catroom.ir"),
    ("http://telegram.org", "http://catroom.ir"),
    ("//telegram.org", "//catroom.ir"),
]

# User-visible brand words. "Telegram Desktop" is the app itself; the bare
# "Telegram" only survives inside hostnames and identifiers, which are not
# user-visible text, so a plain replace is safe in .strings files.
WORD_PAIRS = [
    ("Telegram Desktop", "TheCat"),
    ("Telegram Premium", "TheCat Premium"),
    ("Telegram Stars", "TheCat Stars"),
    ("Telegram Passport", "TheCat Passport"),
    ("Telegram Business", "TheCat Business"),
    ("Telegram and Fragment", "TheCat and Kat Market"),
]

# bare brand word, applied to lang.strings last so compounds above win.
BARE_BRAND_PAIRS = [
    ("Fragment", "Kat Market"),
    ("Telegram", "TheCat"),
]


def rewrite_file(path: pathlib.Path, pairs) -> bool:
    try:
        text = path.read_text(encoding="utf-8")
    except (UnicodeDecodeError, OSError):
        return False
    head, body = split_legal_header(text)
    new = body
    for a, b in pairs:
        new = new.replace(a, b)
    if new == body:
        return False
    path.write_text(head + new, encoding="utf-8")
    return True


LEGAL_MARKERS = (
    "This file is part of Telegram Desktop",
    "the official desktop application for the Telegram",
    "github.com/telegramdesktop/tdesktop",
)


def split_legal_header(text: str) -> tuple[str, str]:
    """Separate the GPL notice from the rest of a source or resource file.

    Telegram Desktop is GPLv3 and its licence header names the upstream
    project. Rebrading those lines would misrepresent the licence, so every
    rewrite skips them and only touches what follows.
    """
    index = 0
    while True:
        newline = text.find("\n", index)
        if newline < 0:
            break
        line = text[index:newline]
        if any(marker in line for marker in LEGAL_MARKERS):
            # Extend to the end of the comment block that contains it.
            end = text.find("*/", newline)
            if end >= 0:
                return text[:end + 2] + "\n", text[end + 2:]
            return text[:newline + 1], text[newline + 1:]
        index = newline + 1
    return "", text


def rewrite_links(src: pathlib.Path) -> None:
    changed = 0
    for base in (src / "Telegram/SourceFiles", src / "Telegram/Resources"):
        for path in base.rglob("*"):
            if not path.is_file() or path.suffix.lower() not in TEXT_EXTS:
                continue
            if rewrite_file(path, LINK_PAIRS):
                changed += 1
                print(f"  links → {path.relative_to(src)}")
    print(f"  rewritten files: {changed}")


def rebrand_strings(src: pathlib.Path) -> None:
    """Replace the brand name in every user-visible string.

    Only Resources/langs is touched: those are the language packs the running
    app displays. Source comments and the LEGAL headers keep their upstream
    text, which the GPL and the "based on Telegram Desktop" notice both
    require.
    """
    langs = src / "Telegram/Resources/langs"
    if not langs.is_dir():
        die(f"missing {langs}")
    changed = 0
    for path in sorted(langs.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in TEXT_EXTS:
            continue
        if rewrite_file(path, WORD_PAIRS + BARE_BRAND_PAIRS):
            changed += 1
            print(f"  brand → {path.relative_to(src)}")
    print(f"  rebranded string files: {changed}")


def rebrand_identity(src: pathlib.Path) -> None:
    """Give TheCat its own single-instance lock, app id and display name.

    cGUIDStr() feeds the /tmp lock server name and the QLockFile path, so while
    it stays upstream's GUID a running Telegram makes TheCat believe another
    copy of itself is open ("This instance of Telegram cannot be opened").
    """
    version_h = src / "Telegram/SourceFiles/core/version.h"
    text = version_h.read_text(encoding="utf-8")
    new = text.replace(
        'constexpr auto AppName = "Telegram Desktop"_cs;',
        'constexpr auto AppName = "TheCat"_cs;',
    ).replace(
        'constexpr auto AppFile = "Telegram"_cs;',
        'constexpr auto AppFile = "TheCat"_cs;',
    ).replace(
        'constexpr auto AppId = "{53F49750-6209-4FBF-9CA8-7A333C87D1ED}"_cs;',
        'constexpr auto AppId = "{9B0C4E31-7F4A-4C63-9DD2-51AB6E0F8C27}"_cs;',
    )
    if new == text:
        die("version.h identity replacements did not match")
    version_h.write_text(new, encoding="utf-8")

    config_h = src / "Telegram/SourceFiles/config.h"
    text = config_h.read_text(encoding="utf-8")
    # Upstream's GUID would collide with a running Telegram Desktop.
    new = text.replace(
        'static const char *gGuidStr = "{87A94AB0-E370-4cde-98D3-ACC110C5967D}";',
        'static const char *gGuidStr = "{3F8A17C4-5D92-4B6E-A1C7-0E24B9D63F58}";',
    )
    if new == text:
        die("config.h gGuidStr replacement did not match")
    config_h.write_text(new, encoding="utf-8")
    print("  identity: TheCat app name, own GUID, own AppId")


def rebrand_cmake_and_plist(src: pathlib.Path) -> None:
    cmake_path = src / "Telegram/CMakeLists.txt"
    cmake = cmake_path.read_text(encoding="utf-8")
    cmake2 = cmake
    cmake2 = cmake2.replace(
        'set(bundle_identifier "com.tdesktop.Telegram$<$<CONFIG:Debug>:Debug>")',
        'set(bundle_identifier "ir.catroom.thecat$<$<CONFIG:Debug>:Debug>")',
    )
    cmake2 = cmake2.replace(
        'set(bundle_identifier "com.tdesktop.Telegram")',
        'set(bundle_identifier "ir.catroom.thecat")',
    )
    cmake2 = cmake2.replace('set(output_name "Telegram")', 'set(output_name "TheCat")')
    cmake2 = cmake2.replace('set(output_name "Telegram Lite")', 'set(output_name "TheCat")')
    # lang_packs is a fixed list copied into Contents/Resources; a language
    # outside it never reaches the bundle, however many .lproj trees exist.
    cmake2 = cmake2.replace(
        "    set(lang_packs\n        en\n        de\n",
        "    set(lang_packs\n        en\n        fa\n        de\n",
    )
    if "        fa\n" not in cmake2:
        die("CMakeLists.txt lang_packs replacement did not match")
    if cmake2 == cmake:
        print("  WARNING: cmake name/bundle replacements did not match")
    else:
        cmake_path.write_text(cmake2, encoding="utf-8")
        print("  cmake: output_name=TheCat bundle=ir.catroom.thecat lang_packs+=fa")

    plist_path = src / "Telegram/Telegram.plist"
    if plist_path.is_file():
        plist = plist_path.read_text(encoding="utf-8")
        plist2 = plist.replace(
            "<string>Telegram Desktop messaging app</string>",
            "<string>TheCat messaging app</string>",
        )
        if plist2 != plist:
            plist_path.write_text(plist2, encoding="utf-8")
            print("  plist: GetInfoString → TheCat")


def add_persian_lproj(src: pathlib.Path) -> None:
    """Note: adding fa.lproj here is not enough for a macOS bundle.

    Telegram/CMakeLists.txt copies a fixed lang_packs list into
    Contents/Resources, so the language has to be listed there as well.
    """
    langs = src / "Telegram/Resources/langs"
    fa = langs / "fa.lproj"
    fa.mkdir(parents=True, exist_ok=True)
    (fa / "InfoPlist.strings").write_bytes(
        'CFBundleDisplayName = "کت";\nCFBundleName = "کت";\n'.encode("utf-8")
    )
    en = langs / "en.lproj/Localizable.strings"
    if en.is_file():
        shutil.copy2(en, fa / "Localizable.strings")
    print(f"  fa.lproj → {fa}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--tdesktop", default=str(ROOT / "tdesktop"),
                        help="path to the tdesktop checkout (default: ./tdesktop)")
    parser.add_argument("--logo", default=str(ROOT / "logo.png"))
    parser.add_argument("--icon", default=str(ROOT / "logo-icon.png"),
                        help="square source for the .app/Dock/tray icon")
    args = parser.parse_args()

    src = pathlib.Path(args.tdesktop).resolve()
    if not (src / "Telegram/CMakeLists.txt").is_file():
        die(f"tdesktop not ready at {src}")

    require_pillow()
    print("== logos ==")
    replace_logos(src, pathlib.Path(args.logo))
    replace_app_icon(src, pathlib.Path(args.icon))
    make_tray_icons(src, pathlib.Path(args.icon))
    print("== links ==")
    rewrite_links(src)
    print("== brand words ==")
    rebrand_strings(src)
    print("== names ==")
    rebrand_identity(src)
    rebrand_cmake_and_plist(src)
    add_persian_lproj(src)
    print("branding done")


if __name__ == "__main__":
    main()
