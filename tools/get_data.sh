#!/bin/sh
# Natural Earth 1:50m land, geography regions (deserts) and glaciated areas
# (public domain, naturalearthdata.com) into data/ne. Only needed to rebuild
# tools/earth_materials.png; the build uses that file when data/ne is absent.
set -e
cd "$(dirname "$0")/../data" 2>/dev/null || { mkdir -p "$(dirname "$0")/../data"; cd "$(dirname "$0")/../data"; }
mkdir -p ne && cd ne
B=https://naciscdn.org/naturalearth/50m
for f in physical/ne_50m_land physical/ne_50m_geography_regions_polys physical/ne_50m_glaciated_areas; do
  n=$(basename $f)
  [ -f $n.shp ] || { curl -fsSLO $B/$f.zip && unzip -oq $n.zip && rm $n.zip; }
done
