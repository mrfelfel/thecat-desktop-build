#!/bin/bash
# Patch + configure + build TheCat Desktop (tdesktop rebranded for catroom.ir).
#
# Usage:  ./build_thecat.sh [--prepare] [--skip-build]
#   --prepare     also download/build the Qt and media libraries (Libraries/,
#                 ThirdParty/) — slow, ~1h on a cold cache
#   --skip-build  stop after configure
#
# Environment overrides:
#   TDESKTOP_SRC   tdesktop checkout      (default: ./tdesktop)
#   BUILD_JOBS     parallel build jobs    (default: all logical CPUs)
set -euo pipefail
export PATH=/usr/bin:/bin:/opt/homebrew/bin:${PATH:-}
unset EMSDK EMSDK_NODE EMSDK_PYTHON

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SRC="${TDESKTOP_SRC:-$ROOT/tdesktop}"
PREPARE=0
SKIP_BUILD=0

for arg in "$@"; do
  case "$arg" in
    --prepare) PREPARE=1 ;;
    --skip-build) SKIP_BUILD=1 ;;
    *) echo "unknown argument: $arg" >&2; exit 2 ;;
  esac
done

if [ ! -f "$SRC/Telegram/CMakeLists.txt" ]; then
  echo "ERROR: tdesktop not found at $SRC" >&2
  exit 1
fi

JOBS="${BUILD_JOBS:-$( (sysctl -n hw.logicalcpu 2>/dev/null || nproc) )}"
BRANDED_SRC="$SRC/Telegram/SourceFiles/mtproto/mtproto_dc_options.cpp"

echo "==> 1/5 patch endpoint + RSA keys"
python3 "$ROOT/patch_thecat_endpoint.py" "$BRANDED_SRC"
grep -n "62.220.127.238" "$BRANDED_SRC"

echo "==> 2/5 brand TheCat / کت + link rewrites"
python3 "$ROOT/brand_thecat.py" --tdesktop "$SRC"

if [ "$PREPARE" = 1 ]; then
  echo "==> 3/5 prepare libraries (Qt + media deps)"
  if [ "$(uname -s)" = "Darwin" ]; then
    bash "$SRC/Telegram/build/prepare/mac.sh"
  else
    bash "$SRC/Telegram/build/prepare/linux.sh"
  fi
else
  echo "==> 3/5 prepare libraries: skipped (pass --prepare to run)"
fi

echo "==> 4/5 configure"
cd "$SRC/Telegram"
# Test-only Telegram API credentials; theCat's server does not validate api_id.
./configure.sh -D TDESKTOP_API_ID=17349 -D TDESKTOP_API_HASH=344583e45741c457fe1862106095a5eb

if [ "$SKIP_BUILD" = 1 ]; then
  echo "==> 5/5 build: skipped (--skip-build)"
  exit 0
fi

echo "==> 5/5 build Release ($JOBS jobs)"
cd "$SRC"
cmake --build out --config Release --target Telegram -j"$JOBS"

echo "==> done"
ls -la "$SRC/out/Release/" | head
ls -la "$SRC/out/Release/TheCat.app/Contents/MacOS/" 2>/dev/null \
  || ls -la "$SRC/out/Release/" | head
