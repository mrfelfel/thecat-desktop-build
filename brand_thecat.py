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
    become a solid block. Only dark pixels of the logo count as the mark; they
    are written as a soft alpha mask over flat black, which `template` mode
    then recolours. Keeping the alpha channel is what makes it a silhouette
    instead of a square.
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
    from PIL import Image
    with Image.open(logo) as source:
        img = source.convert("RGBA").resize((size, size), Image.LANCZOS)
    # Dark-on-light logo: the mark is what is darker than mid grey.
    mask = Image.new("L", (size, size))
    src_px, mask_px = img.load(), mask.load()
    for y in range(size):
        for x in range(size):
            r, g, b, a = src_px[x, y]
            lum = (r * 299 + g * 587 + b * 114) // 1000
            # The mark is dark against a light background; anything lighter
            # than mid grey is background and must not be inked.
            mask_px[x, y] = int(a * max(0, 160 - lum) / 160)
    out = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    out.putalpha(mask)
    out.save(target)


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


def rewrite_links(src: pathlib.Path) -> None:
    pairs = [
        ("https://telegram.org", "https://catroom.ir"),
        ("http://telegram.org", "http://catroom.ir"),
        ("https://t.me/", "https://cr0.ir/"),
        ("http://t.me/", "http://cr0.ir/"),
        ("//telegram.org", "//catroom.ir"),
        ("//t.me/", "//cr0.ir/"),
    ]
    changed = 0
    for base in (src / "Telegram/SourceFiles", src / "Telegram/Resources"):
        for path in base.rglob("*"):
            if not path.is_file() or path.suffix.lower() not in TEXT_EXTS:
                continue
            try:
                text = path.read_text(encoding="utf-8")
            except (UnicodeDecodeError, OSError):
                continue
            new = text
            for a, b in pairs:
                new = new.replace(a, b)
            if new != text:
                path.write_text(new, encoding="utf-8")
                changed += 1
                print(f"  links → {path.relative_to(src)}")
    print(f"  rewritten files: {changed}")


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
    if cmake2 == cmake:
        print("  WARNING: cmake name/bundle replacements did not match")
    else:
        cmake_path.write_text(cmake2, encoding="utf-8")
        print("  cmake: output_name=TheCat bundle=ir.catroom.thecat")

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
    print("== names ==")
    rebrand_identity(src)
    rebrand_cmake_and_plist(src)
    add_persian_lproj(src)
    print("branding done")


if __name__ == "__main__":
    main()
