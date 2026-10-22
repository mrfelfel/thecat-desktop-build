#!/usr/bin/env python3
"""Brand official TDesktop as TheCat (en) / کت (fa).
- logos: Resources/art/icon* + logo* ← user logo.png
- links: telegram.org → catroom.ir, t.me → cr0.ir
- names: output_name TheCat, bundle ir.catroom.thecat, fa.lproj display name کت
"""
from __future__ import annotations

import pathlib
import re
import shutil
import subprocess
import sys

ROOT = pathlib.Path("/Volumes/SADDISK/owpengram-build")
SRC = ROOT / "tdesktop"
LOGO = ROOT / "logo.png"
ART = SRC / "Telegram/Resources/art"
SRCFILES = SRC / "Telegram/SourceFiles"
CMAKE = SRC / "Telegram/CMakeLists.txt"
PLIST = SRC / "Telegram/Telegram.plist"
LANGS = SRC / "Telegram/Resources/langs"


def die(msg: str) -> None:
    print("ERROR:", msg, file=sys.stderr)
    sys.exit(1)


def replace_logos() -> None:
    if not LOGO.is_file():
        die(f"missing logo {LOGO}")
    targets = []
    for path in ART.rglob("*"):
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
            # keep windows .ico as png bytes won't be a valid ico; skip
            print(f"  skip ico {path.name}")
            continue
        # Preserve dimensions by re-encoding the user logo into the same size.
        try:
            out = subprocess.check_output(
                ["sips", "-g", "pixelWidth", "-g", "pixelHeight", str(path)],
                text=True,
            )
            w = re.search(r"pixelWidth:\s*(\d+)", out).group(1)
            h = re.search(r"pixelHeight:\s*(\d+)", out).group(1)
            subprocess.check_call(
                [
                    "sips",
                    "-z",
                    h,
                    w,
                    str(LOGO),
                    "--out",
                    str(path),
                ],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            print(f"  logo → {path.relative_to(SRC)} ({w}x{h})")
        except Exception as e:  # noqa: BLE001
            print(f"  FAILED {path}: {e}")
            raise


TEXT_EXTS = {".cpp", ".h", ".mm", ".m", ".pl", ".py", ".json", ".md", ".txt", ".cmake", ".html", ".js", ".css", ".strings"}


def rewrite_links() -> None:
    # Domain rewrites requested by the operator.
    pairs = [
        ("https://telegram.org", "https://catroom.ir"),
        ("http://telegram.org", "http://catroom.ir"),
        ("https://t.me/", "https://cr0.ir/"),
        ("http://t.me/", "http://cr0.ir/"),
        ("tg://resolve", "tg://resolve"),  # keep tg scheme for local handlers
    ]
    changed = 0
    for base in (SRCFILES, SRC / "Telegram/Resources"):
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
            # bare telegram.org / t.me host mentions in URLs already covered;
            # also catch protocol-relative //telegram.org
            new = new.replace("//telegram.org", "//catroom.ir")
            new = new.replace("//t.me/", "//cr0.ir/")
            if new != text:
                path.write_text(new, encoding="utf-8")
                changed += 1
                print(f"  links → {path.relative_to(SRC)}")
    print(f"  rewritten files: {changed}")


def rebrand_cmake_and_plist() -> None:
    cmake = CMAKE.read_text(encoding="utf-8")
    cmake2 = cmake
    cmake2 = cmake2.replace('set(bundle_identifier "com.tdesktop.Telegram$<$<CONFIG:Debug>:Debug>")',
                            'set(bundle_identifier "ir.catroom.thecat$<$<CONFIG:Debug>:Debug>")')
    cmake2 = cmake2.replace('set(bundle_identifier "com.tdesktop.Telegram")',
                            'set(bundle_identifier "ir.catroom.thecat")')
    cmake2 = cmake2.replace('set(output_name "Telegram")', 'set(output_name "TheCat")')
    cmake2 = cmake2.replace('set(output_name "Telegram Lite")', 'set(output_name "TheCat")')
    if cmake2 == cmake:
        print("  WARNING: cmake name/bundle replacements did not match")
    else:
        CMAKE.write_text(cmake2, encoding="utf-8")
        print("  cmake: output_name=TheCat bundle=ir.catroom.thecat")

    plist = PLIST.read_text(encoding="utf-8")
    plist2 = plist.replace(
        "<string>Telegram Desktop messaging app</string>",
        "<string>TheCat messaging app</string>",
    )
    # Prefer TheCat for default (non-localized) display name in URL handler list.
    plist2 = plist2.replace("<string>tg</string>", "<string>tg</string>")
    if plist2 != plist:
        PLIST.write_text(plist2, encoding="utf-8")
        print("  plist: GetInfoString → TheCat")


def add_persian_lproj() -> None:
    fa = LANGS / "fa.lproj"
    fa.mkdir(parents=True, exist_ok=True)
    # macOS localized app name
    (fa / "InfoPlist.strings").write_bytes(
        "CFBundleDisplayName = \"کت\";\nCFBundleName = \"کت\";\n".encode("utf-8")
    )
    # Copy en Localizable as a base so the folder is complete; server langpack
    # supplies real translations after login.
    en = LANGS / "en.lproj/Localizable.strings"
    if en.is_file():
        shutil.copy2(en, fa / "Localizable.strings")
    print(f"  fa.lproj → {fa}")


def main() -> None:
    if not (SRC / "Telegram/CMakeLists.txt").is_file():
        die(f"tdesktop not ready at {SRC}")
    print("== logos ==")
    replace_logos()
    print("== links ==")
    rewrite_links()
    print("== names ==")
    rebrand_cmake_and_plist()
    add_persian_lproj()
    print("branding done")


if __name__ == "__main__":
    main()
