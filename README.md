<div dir="ltr">

# 🐱 TheCat Desktop

**TheCat — «کت» — a clean, fast desktop messenger for the catroom.ir community.**

TheCat Desktop is a standalone desktop messenger built for the **catroom.ir**
platform. It focuses on everyday messaging and community life: private chats
and groups, channels, voice messages, voice and video calls, stickers, gifts
and premium features — wrapped in its own name, colours and identity.

One place for messaging, games and entertainment, in Persian and English.

> The Persian name is **کت** (*cat*) — hence *TheCat*.

---

## Download

| Platform | Where |
|---|---|
| 🪟 Windows x64 | Repo **Actions** → workflow **TheCat Windows** → latest run → artifact `TheCat-windows-x64` |
| 🍎 macOS (Apple Silicon) | **Releases**, or artifact `TheCat-macos-arm64` from the **TheCat macOS** workflow |

*(Runs start on GitHub-hosted runners — the first build is slower, later ones
reuse caches.)*

**Requirements to run:** Windows 10 or newer; macOS 11 or newer (Apple Silicon).

Just open the downloaded app file:

- **Windows:** unzip the artifact, run `TheCat.exe`
- **macOS:** unzip, drag **TheCat.app** into Applications, right-click → *Open*
  the first time so Gatekeeper lets it through (not notarized)

Then sign in with your phone number and you're in.

---

## What's in this repository

```
brand_thecat.py           logos, links and app name → TheCat / کت
patch_thecat_endpoint.py  built-in DCs + RSA keys for the catroom.ir server
build_thecat.sh           patch → brand → prepare → configure → build
logo.png / logo.svg       app artwork
tdesktop/                 Telegram Desktop source (GPLv3), vendored in full
.github/workflows/        TheCat Windows / TheCat macOS CI
```

The `tdesktop/` tree is the complete upstream Telegram Desktop source with all
its submodules **vendored as regular files**, so a plain `git clone` is a
complete, buildable tree — no `--recursive`, no network fetches for libraries.
The upstream `.gitmodules` files are kept only as provenance notes; git does
not treat the directories as submodules.

---

## Build it yourself

### Requirements

- **Windows:** Visual Studio 2022/2026 Build Tools with the Desktop C++ workload
- **macOS:** Xcode command line tools + [Homebrew](https://brew.sh)
- Git, CMake 3.22+, Python 3
- ~55 GB of free disk space (Qt and media libraries are built from source)

### macOS / Linux (local build)

```bash
git clone https://github.com/mrfelfel/thecat-desktop-build.git
cd thecat-desktop-build

# Full build, including Qt and media libraries from source:
./build_thecat.sh --prepare

# Or, if you already have Libraries/ and ThirdParty/ prepared:
./build_thecat.sh
```

Result: `tdesktop/out/Release/TheCat.app`.

Equivalent manual steps:

```bash
python3 patch_thecat_endpoint.py
python3 brand_thecat.py
(cd tdesktop/Telegram && ../build/prepare/mac.sh)   # or linux.sh
(cd tdesktop/Telegram && ./configure.sh \
   -D TDESKTOP_API_ID=17349 \
   -D TDESKTOP_API_HASH=344583e45741c457fe1862106095a5eb)
cmake --build tdesktop/out --config Release --target Telegram
```

### Windows (CI)

Push to `main`, or start workflow **TheCat Windows** manually from the
**Actions** tab. Output: `TheCat.exe` in the build artifact.

`deploy/prepare-win.bat` is the Windows entry point used by CI: it patches,
brands, prepares the libraries and configures the project.

---

## Why open source?

TheCat Desktop is built on [Telegram Desktop][tdesktop], which is licensed
under the [GNU GPL v3][gpl]. That license is not a formality — it obliges us to
publish the source of the app we ship, including every modification made for
TheCat. So this repository exists first because **the license requires it**: a
closed binary built from GPL code would violate the rights of its authors and
of everyone who uses it.

Beyond compliance, publishing the source buys real value:

- **Transparency.** Anyone — users, auditors, researchers — can read the code
  that runs on their machine, check what it connects to and validate that the
  app does what it claims. Messaging software is exactly where that matters
  most.
- **Trust you can verify.** A claim of privacy is cheap. A repository you can
  clone, inspect and rebuild is not. The build is reproducible from this tree.
- **Freedom to continue.** Users can learn from it, adapt it, fix bugs and
  keep the app alive on their own terms — nobody can take a working messenger
  away by shutting down one company.
- **Room for contribution.** Fixes, translations, packaging and improvements
  from anyone can be reviewed openly and merged into future releases.

Open source here isn't a marketing move; it's the only published form a
GPL-derived messenger may legitimately take, and the most honest way to ship
this app — because you can verify it yourself on your own machine.

---

## Support & community

- 🌐 **Website / support:** [catroom.ir][catroom]
- 🐱 **TheCat (کت)** — the messenger itself, right here

Questions, issues and feedback go through [catroom.ir][catroom].

---

## License

Licensed under the [GNU GPL v3][gpl], inherited from
[Telegram Desktop][tdesktop]. Modifications and branding shipped as TheCat are
distributed under the same license.

Telegram and Telegram Desktop are trademarks of Telegram FZ-LLC. This project
is independent and not affiliated with, endorsed by, or connected to the
official Telegram services.

[gpl]: https://www.gnu.org/licenses/gpl-3.0.en.html
[tdesktop]: https://github.com/telegramdesktop/tdesktop
[catroom]: https://catroom.ir

</div>
