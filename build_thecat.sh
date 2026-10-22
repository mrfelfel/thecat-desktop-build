#!/bin/bash
# Patch + configure + build official TDesktop for theCat (62.220.127.238:30001).
# Run after the recursive clone finishes.
set -euo pipefail
export PATH=/usr/bin:/bin:/opt/homebrew/bin
unset EMSDK EMSDK_NODE EMSDK_PYTHON

ROOT=/Volumes/SADDISK/owpengram-build
SRC=$ROOT/tdesktop
cd "$SRC"

echo "==> 1/5 patch mtproto_dc_options.cpp"
python3 "$ROOT/patch_thecat_endpoint.py" "$SRC/Telegram/SourceFiles/mtproto/mtproto_dc_options.cpp"
grep -n "62.220.127.238" "$SRC/Telegram/SourceFiles/mtproto/mtproto_dc_options.cpp"
grep -n "2LnOaBr" "$SRC/Telegram/SourceFiles/mtproto/mtproto_dc_options.cpp"

echo "==> 2/5 brand TheCat / کت + link rewrites"
python3 "$ROOT/brand_thecat.py"

echo "==> 3/5 prepare libraries (Qt + deps)"
# prepare/mac.sh downloads/builds ../Libraries relative to Telegram/
bash "$SRC/Telegram/build/prepare/mac.sh"

echo "==> 4/5 configure"
cd "$SRC/Telegram"
# Test-only Telegram API credentials; telesrv does not validate api_id.
./configure.sh -D TDESKTOP_API_ID=17349 -D TDESKTOP_API_HASH=344583e45741c457fe1862106095a5eb

echo "==> 5/5 build Release"
cd "$SRC"
cmake --build out --config Release --target Telegram -j"$(sysctl -n hw.logicalcpu)"

echo "==> done: $(ls -la "$SRC/out/Release/" | head)"
ls -la "$SRC/out/Release/Telegram.app/Contents/MacOS/" 2>/dev/null || ls -la "$SRC/out/Release/" | head
