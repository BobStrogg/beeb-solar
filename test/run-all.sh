#!/bin/sh
# build, then the headless and browser tests (serves web/ on :8767)
set -e
cd "$(dirname "$0")/.."
./build.sh >/dev/null && cp build/beeb-solar.ssd web/jsbeeb/discs/
node test/boot.mjs
(cd web && python3 -m http.server 8767 >/dev/null 2>&1) & S=$!
sleep 1; node test/browser.mjs; kill $S
