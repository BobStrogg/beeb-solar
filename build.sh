#!/bin/sh
# Build build/beeb-solar.ssd (and the MMB image) from src/.
set -e
cd "$(dirname "$0")"
mkdir -p build
BEEBASM=${BEEBASM:-vendor/beebasm-src/beebasm}
${PYTHON:-python3} tools/gen_tables.py
(cd src && ../$BEEBASM -i solar.6502 -do ../build/beeb-solar.ssd -opt 3 -title BEEB-SOLAR -v > ../build/listing.txt 2>&1) || { grep -i -B2 -A2 error build/listing.txt; exit 1; }
grep -E "^(code\+data|vars)" build/listing.txt
