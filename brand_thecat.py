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
import re
import shutil
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent


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
            out = subprocess.check_output(
                ["sips", "-g", "pixelWidth", "-g", "pixelHeight", str(path)],
                text=True,
            )
            w = re.search(r"pixelWidth:\s*(\d+)", out).group(1)
            h = re.search(r"pixelHeight:\s*(\d+)", out).group(1)
            subprocess.check_call(
                ["sips", "-z", h, w, str(logo), "--out", str(path)],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            print(f"  logo → {path.relative_to(src)} ({w}x{h})")
        except Exception as e:  # noqa: BLE001
            print(f"  FAILED {path}: {e}")
            raise


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
    args = parser.parse_args()

    src = pathlib.Path(args.tdesktop).resolve()
    if not (src / "Telegram/CMakeLists.txt").is_file():
        die(f"tdesktop not ready at {src}")

    print("== logos ==")
    replace_logos(src, pathlib.Path(args.logo))
    print("== links ==")
    rewrite_links(src)
    print("== names ==")
    rebrand_cmake_and_plist(src)
    add_persian_lproj(src)
    print("branding done")


if __name__ == "__main__":
    main()
