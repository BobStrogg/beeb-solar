#!/bin/sh
# build/BEEB-SOLAR.MMB: a 511-slot MMFS image with BEEB-SOLAR in slot 0 (boots with
# SHIFT+BREAK), zipped with the .ssd as build/BEEB-SOLAR.MMB.zip
set -e
cd "$(dirname "$0")/.."
U=vendor/MMB_Utils
rm -f build/BEEB-SOLAR.MMB
perl $U/dblank_mmb.pl -f build/BEEB-SOLAR.MMB >/dev/null
perl $U/dput_ssd.pl -f build/BEEB-SOLAR.MMB 0 build/beeb-solar.ssd
perl $U/donboot.pl -f build/BEEB-SOLAR.MMB 0 0 >/dev/null
python3 - <<'PY'
import zipfile
with zipfile.ZipFile("build/BEEB-SOLAR.MMB.zip", "w", zipfile.ZIP_DEFLATED) as z:
    z.write("build/BEEB-SOLAR.MMB", "BEEB-SOLAR.MMB"); z.write("build/beeb-solar.ssd", "beeb-solar.ssd")
PY
ls -l build/BEEB-SOLAR.MMB.zip
