#!/bin/sh
# Refresh vendored pygbag CDN (run when bumping pygbag version).
set -eu
ROOT="$(CDPATH= cd -- "$(dirname "$0")" && pwd)"
CDN_ROOT="$ROOT/cdn"
VER="${1:-0.9.3}"
BASE="https://pygame-web.github.io/cdn"
UA="Mozilla/5.0 (compatible; Lena2Build/1.0)"

rm -rf "$CDN_ROOT"
mkdir -p "$CDN_ROOT/$VER/cpython312" "$CDN_ROOT/vt"

dl() {
  dest="$2"
  mkdir -p "$(dirname "$dest")"
  curl -fsSL -A "$UA" -o "$dest" "$1"
  echo "ok $dest ($(wc -c < "$dest"))"
}

dl "$BASE/$VER/pythons.js" "$CDN_ROOT/$VER/pythons.js"
dl "$BASE/$VER/cpythonrc.py" "$CDN_ROOT/$VER/cpythonrc.py"
dl "$BASE/$VER/empty.ogg" "$CDN_ROOT/$VER/empty.ogg"
printf '%s\n' '<!DOCTYPE html><html><head><meta charset="utf-8"></head><body></body></html>' \
  > "$CDN_ROOT/$VER/empty.html"

for f in main.js main.wasm main.data; do
  dl "$BASE/$VER/cpython312/$f" "$CDN_ROOT/$VER/cpython312/$f"
done

dl "$BASE/vtx.js" "$CDN_ROOT/vtx.js"
dl "$BASE/vt.js" "$CDN_ROOT/vt.js"
for f in xterm.css xterm.js xterm-addon-image.js; do
  dl "$BASE/vt/$f" "$CDN_ROOT/vt/$f"
done

dl "https://pygame-web.github.io/archives/0.9/browserfs.min.js" "$ROOT/browserfs.min.js"
du -sh "$CDN_ROOT"
