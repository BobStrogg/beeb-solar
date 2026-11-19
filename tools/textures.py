"""Planet textures for BEEB-SOLAR: 128x64 equirectangular maps of material
indices (0-7), a palette (material -> teletext colour) per body, and dither
probabilities that the 6502 unpacker uses to add noise at load time.

Row 0 is latitude +90, column 0 is longitude -180 (west), so u grows to the
east. Earth's land, deserts and ice come from Natural Earth (public domain).
"""
import numpy as np, os, math
from PIL import Image, ImageDraw

W, H = 128, 64
RED, GREEN, YELLOW, BLUE, MAGENTA, CYAN, WHITE = 1, 2, 3, 4, 5, 6, 7
COLRGB = {0: (0, 0, 0), 1: (255, 0, 0), 2: (0, 255, 0), 3: (255, 255, 0), 4: (0, 0, 255), 5: (255, 0, 255), 6: (0, 255, 255), 7: (255, 255, 255)}
HERE = os.path.dirname(os.path.abspath(__file__))
NE = os.path.join(HERE, "..", "data", "ne")
rng = np.random.default_rng(1977)

lat = 90 - (np.arange(H) + 0.5) * 180 / H            # per row
lon = -180 + (np.arange(W) + 0.5) * 360 / W          # per column
LON, LAT = np.meshgrid(lon, lat)


def raster(shpname, scale=8, filt=None):
    """fraction of each texel covered by the shapefile's polygons"""
    import shapefile
    r = shapefile.Reader(os.path.join(NE, shpname))
    img = Image.new("L", (W * scale, H * scale), 0)
    d = ImageDraw.Draw(img)
    for sr in r.iterShapeRecords():
        if filt and not filt(sr.record):
            continue
        shp = sr.shape
        parts = list(shp.parts) + [len(shp.points)]
        for a, b in zip(parts[:-1], parts[1:]):
            pts = [((x + 180) / 360 * W * scale, (90 - y) / 180 * H * scale) for x, y in shp.points[a:b]]
            if len(pts) > 2:
                d.polygon(pts, fill=255)
    a = np.asarray(img, dtype=np.float32) / 255
    return a.reshape(H, scale, W, scale).mean(axis=(1, 3))


def ang(lon1, lat1, lon2, lat2):
    """great-circle distance in degrees"""
    l1, p1, l2, p2 = map(np.radians, (lon1, lat1, lon2, lat2))
    c = np.sin(p1) * np.sin(p2) + np.cos(p1) * np.cos(p2) * np.cos(l1 - l2)
    return np.degrees(np.arccos(np.clip(c, -1, 1)))


def blob(lon0, lat0, rlon, rlat):
    """elliptical region (degrees) with longitude wrap"""
    dl = (LON - lon0 + 180) % 360 - 180
    return (dl / rlon) ** 2 + ((LAT - lat0) / rlat) ** 2 < 1


def noise(scale_x, scale_y, octaves=3, seed=0):
    g = np.random.default_rng(seed)
    out = np.zeros((H, W))
    for o in range(octaves):
        sx, sy = max(1, int(scale_x * 2 ** o)), max(1, int(scale_y * 2 ** o))
        base = g.random((sy + 1, sx))
        base = np.concatenate([base, base[:, :1]], axis=1)       # wrap in longitude
        ys = np.linspace(0, sy, H); xs = np.linspace(0, sx, W, endpoint=False)
        yi = np.minimum(ys.astype(int), sy - 1); yf = ys - yi
        xi = xs.astype(int); xf = xs - xi
        yf = yf * yf * (3 - 2 * yf); xf = xf * xf * (3 - 2 * xf)
        a = base[yi][:, xi] * (1 - xf) + base[yi][:, xi + 1] * xf
        b = base[yi + 1][:, xi] * (1 - xf) + base[yi + 1][:, xi + 1] * xf
        out += (a * (1 - yf[:, None]) + b * yf[:, None]) / 2 ** o
    return out / out.max()


# ---------------------------------------------------------------- bodies
# each returns (materials HxW uint8, palette[8], dither[8] (0-255, 0 = none), fgmode)
EARTH_CACHE = os.path.join(HERE, "earth_materials.png")


def earth():
    """from Natural Earth when data/ne has it (tools/get_data.sh), else from
    the committed 128x64 result of that (tools/earth_materials.png)"""
    pal = [BLUE, GREEN, YELLOW, WHITE, WHITE, CYAN, GREEN, WHITE]
    if not os.path.exists(os.path.join(NE, "ne_50m_land.shp")):
        return np.asarray(Image.open(EARTH_CACHE), dtype=np.uint8), pal, [0] * 8, False
    land = raster("ne_50m_land")
    desert = raster("ne_50m_geography_regions_polys", filt=lambda r: r["FEATURECLA"] == "Desert")
    ice = raster("ne_50m_glaciated_areas")
    m = np.zeros((H, W), np.uint8)                         # 0 ocean
    isl = land > 0.42
    m[isl] = 1                                             # land
    m[isl & (desert > 0.3)] = 2                            # desert
    m[(ice > 0.35)] = 3                                    # ice sheets / glaciers
    m[(LAT < -62) & isl] = 3                               # Antarctica
    m[LAT > 79] = 3                                        # Arctic sea ice
    m[(LAT > 72) & (land > 0.2)] = 3                       # high Arctic islands
    Image.fromarray(m, "L").save(EARTH_CACHE)
    return m, pal, [0] * 8, False


def sun():
    n = noise(8, 4, 2, seed=5)
    m = np.full((H, W), 1, np.uint8)                       # granulation: red flecks (dithered)
    m[n < 0.35] = 2                                        # brighter regions: white flecks (dithered)
    m[n > 0.8] = 5                                         # active regions: denser red
    # sunspot groups at mid latitudes
    for lo, la, rx, ry in [(-120, 18, 7, 4), (-100, 15, 4, 3), (10, -14, 6, 4), (25, -16, 3, 2.5), (130, 22, 5, 3), (75, -25, 3, 3)]:
        m[blob(lo, la, rx * 1.6, ry * 1.6)] = 3            # penumbra (flicker)
        m[blob(lo, la, rx * 0.8, ry * 0.8)] = 4            # umbra
    pal = [YELLOW, RED, WHITE, RED, RED, RED, YELLOW, YELLOW]
    dith = [0, 34, 40, 150, 0, 75, 0, 0]
    return m, pal, dith, False


def mercury():
    m = np.full((H, W), 1, np.uint8)                       # surface (dithered grey)
    g = np.random.default_rng(11)
    for _ in range(38):
        lo, la = g.uniform(-180, 180), np.degrees(np.arcsin(g.uniform(-1, 1)))
        r = g.choice([4, 5, 7, 9, 12, 15])
        d = ang(LON, LAT, lo, la)
        m[(d < r * 1.25) & (d >= r * 0.85)] = 3            # bright rim
        m[d < r * 0.85] = 2                                # floor (darker)
    m[ang(LON, LAT, 170, 30) < 22] = 2                     # Caloris basin
    m[(ang(LON, LAT, 170, 30) < 26) & (ang(LON, LAT, 170, 30) >= 22)] = 3
    pal = [0, WHITE, WHITE, WHITE, WHITE, WHITE, WHITE, WHITE]
    dith = [0, 205, 45, 0, 0, 0, 0, 0]
    return m, pal, dith, True


def moon():
    m = np.full((H, W), 1, np.uint8)                       # highlands
    # maria on the near side (centred on longitude 0)
    for lo, la, rx, ry in [(-15, 33, 22, 14), (17, 28, 10, 8), (31, 8, 13, 11), (59, 17, 7, 5), (-38, 10, 25, 14), (-17, -21, 13, 9), (35, -8, 9, 6), (52, -3, 7, 6), (-50, 30, 10, 8)]:
        m[blob(lo, la, rx, ry)] = 2
    g = np.random.default_rng(7)
    for _ in range(26):
        lo, la = g.uniform(-180, 180), np.degrees(np.arcsin(g.uniform(-1, 1)))
        r = g.choice([3, 4, 6, 8])
        d = ang(LON, LAT, lo, la)
        m[(d < r * 1.25) & (d >= r * 0.8)] = 3
    d = ang(LON, LAT, -11, -43); m[d < 4] = 3              # Tycho
    m[(d < 40) & (d > 6) & (np.abs(((LON + 11 + 180) % 30) - 15) < 1.2) & (m == 1)] = 3   # Tycho rays
    pal = [0, WHITE, WHITE, WHITE, WHITE, WHITE, WHITE, WHITE]
    dith = [0, 215, 50, 0, 0, 0, 0, 0]
    return m, pal, dith, True


def venus():
    n = noise(6, 10, 3, seed=3)
    m = np.zeros((H, W), np.uint8)                         # yellow cloud deck
    # Y-shaped / chevron cloud bands that sweep with latitude
    sweep = np.sin(np.radians(LON * 2 + np.abs(LAT) * 2.2) ) * 0.5 + 0.5
    m[(sweep * 0.6 + n * 0.6) > 0.78] = 1                  # white streaks
    m[(sweep * 0.6 + n * 0.6) < 0.25] = 2                  # darker streaks (dithered)
    m[np.abs(LAT) > 70] = 1                                # bright polar collars
    pal = [YELLOW, WHITE, WHITE, YELLOW, YELLOW, YELLOW, YELLOW, YELLOW]
    dith = [0, 0, 90, 0, 0, 0, 0, 0]
    return m, pal, dith, False


def mars():
    n = noise(10, 6, 3, seed=9)
    m = np.zeros((H, W), np.uint8)                         # red-orange plains
    dark = np.zeros((H, W), bool)
    for lo, la, rx, ry in [
        (70, 8, 9, 16),       # Syrtis Major
        (20, -6, 40, 6),      # Sinus Sabaeus / Meridiani
        (-5, -3, 9, 5),       # Sinus Meridiani
        (-30, -25, 30, 10),   # Mare Erythraeum
        (-30, 45, 22, 10),    # Mare Acidalium
        (115, 45, 25, 9),     # Utopia
        (140, -22, 35, 8),    # Mare Cimmerium / Sirenum
        (100, -15, 15, 8),    # Mare Tyrrhenum
        (-85, -27, 9, 6),     # Solis Lacus
        (-150, -30, 15, 7),   # Mare Sirenum
        (-90, 55, 40, 5),     # northern dark collar
    ]:
        dark |= blob(lo, la, rx, ry)
    dark &= n > 0.25
    m[dark] = 1                                            # dark albedo (magenta)
    m[blob(-70, -10, 22, 2.2)] = 1                         # Valles Marineris
    m[blob(70, -42, 14, 10)] = 2                           # Hellas (bright)
    m[blob(20, -45, 12, 6)] = 2                            # Argyre-ish / Noachis bright
    m[blob(-120, 8, 25, 14) & (n > 0.5)] = 2               # Tharsis bright
    m[blob(-134, 18, 3.5, 3.5)] = 1                        # Olympus Mons
    m[LAT > 78] = 3                                        # north polar cap
    m[(LAT > 71) & (n > 0.55)] = 3
    m[LAT < -80] = 3                                       # south polar cap
    m[(LAT < -74) & (n > 0.6)] = 3
    m[(m == 0) & (n > 0.72)] = 4                           # dusty mottling (dithered)
    pal = [RED, MAGENTA, YELLOW, WHITE, YELLOW, RED, RED, RED]
    dith = [0, 0, 0, 0, 110, 0, 0, 0]
    return m, pal, dith, False


def jupiter():
    m = np.zeros((H, W), np.uint8)                         # 0 white zones
    n = noise(16, 8, 3, seed=21)
    wob = (n - 0.5) * 3.0 + np.sin(np.radians(LON * 4)) * 0.8
    L = LAT + wob
    belt = lambda a, b: (L > a) & (L < b)
    m[belt(-60, 60) & ~belt(-20, 20)] = 0
    m[belt(7, 18)] = 1                                     # North Equatorial Belt
    m[belt(-20, -8)] = 1                                   # South Equatorial Belt
    m[belt(24, 30)] = 1                                    # North Temperate Belt
    m[belt(-32, -27)] = 1                                  # South Temperate Belt
    m[belt(18, 24) | belt(-27, -20)] = 2                   # tropical zones (yellow)
    m[np.abs(L) > 38] = 2                                  # polar regions (yellow)
    m[np.abs(L) > 52] = 4                                  # polar hoods (dithered)
    m[(m == 0) & belt(-4, 4) & (n > 0.62)] = 5             # equatorial festoons
    edge = (belt(5, 8) | belt(-8, -5) | belt(17, 19)) & (n > 0.45)
    m[edge] = 3                                            # turbulent belt edges (dithered)
    grs_d = ((LON - 40) / 13) ** 2 + ((LAT + 22) / 6) ** 2
    m[grs_d < 1.7] = 0                                     # Red Spot Hollow
    m[grs_d < 1] = 6                                       # Great Red Spot
    for lo in (-150, -90, -30, 100, 160):
        m[(((LON - lo) / 4) ** 2 + ((LAT + 34) / 2.5) ** 2) < 1] = 0   # white ovals
    pal = [WHITE, RED, YELLOW, RED, YELLOW, YELLOW, RED, WHITE]
    dith = [0, 0, 0, 130, 120, 140, 0, 0]
    return m, pal, dith, False


def saturn():
    m = np.zeros((H, W), np.uint8)                         # 0 pale yellow
    n = noise(12, 6, 2, seed=31)
    L = LAT + (n - 0.5) * 1.5
    m[(L > 12) & (L < 20)] = 1                             # belts (sparse red: tan)
    m[(L < -12) & (L > -20)] = 1
    m[(L > 30) & (L < 36)] = 2                             # fainter belts
    m[(L < -30) & (L > -36)] = 2
    m[np.abs(L) > 64] = 3                                  # polar (cyan, the hexagon's haze)
    m[(np.abs(L) < 6) & (n > 0.6)] = 4                     # equatorial white clouds
    pal = [YELLOW, RED, RED, CYAN, WHITE, YELLOW, YELLOW, YELLOW]
    dith = [0, 70, 35, 150, 60, 0, 0, 0]
    return m, pal, dith, False


def uranus():
    n = noise(8, 6, 2, seed=41)
    m = np.zeros((H, W), np.uint8)                         # cyan
    m[(LAT > 60) & (n > 0.3)] = 3                          # polar haze (dithered white)
    m[LAT > 78] = 2
    m[(np.abs(LAT + 20) < 3) & (n > 0.55)] = 2             # faint band (dithered)
    m[(((LON - 60) / 6) ** 2 + ((LAT - 30) / 3) ** 2) < 1] = 1   # a bright cloud
    pal = [CYAN, WHITE, WHITE, WHITE, CYAN, CYAN, CYAN, CYAN]
    dith = [0, 0, 70, 45, 0, 0, 0, 0]
    return m, pal, dith, False


def neptune():
    n = noise(12, 8, 3, seed=51)
    m = np.zeros((H, W), np.uint8)                         # blue
    m[(np.abs(LAT + 25) < 5)] = 1                          # cyan band
    m[(np.abs(LAT - 30) < 4) & (n > 0.4)] = 1
    m[((LON + 20) / 14) ** 2 + ((LAT + 20) / 7) ** 2 < 1] = 2      # Great Dark Spot (magenta)
    m[((LON + 20) / 9) ** 2 + ((LAT + 12) / 2) ** 2 < 1] = 3       # companion clouds
    for lo, la, rx in [(60, -42, 14), (-120, 25, 18), (150, -55, 10), (-60, 45, 12)]:
        m[(((LON - lo) / rx) ** 2 + ((LAT - la) / 1.6) ** 2) < 1] = 3   # white streaks ("scooter")
    m[(np.abs(LAT) > 65)] = 4                              # dithered polar haze
    pal = [BLUE, CYAN, MAGENTA, WHITE, CYAN, BLUE, BLUE, BLUE]
    dith = [0, 0, 0, 0, 100, 0, 0, 0]
    return m, pal, dith, False


BODIES = ["sun", "mercury", "venus", "earth", "mars", "jupiter", "saturn", "uranus", "neptune", "moon"]


def all_textures():
    return {b: globals()[b]() for b in BODIES}


def dither(m, dith, seed=0):
    """what the 6502 unpacker does: a texel of a dithered material keeps its
    material with probability dith/256, else it becomes 0"""
    g = np.random.default_rng(seed)
    out = m.copy()
    p = np.array(dith)[m]
    out[(p > 0) & (g.integers(0, 256, m.shape) >= p)] = 0
    return out


def preview(name, tex, path, scale=4):
    m, pal, dith, fg = tex
    d = dither(m, dith)
    rgb = np.zeros((H, W, 3), np.uint8)
    for k in range(8):
        rgb[d == k] = COLRGB[0 if (fg and k == 0) else pal[k]]
    Image.fromarray(rgb).resize((W * scale, H * scale), Image.NEAREST).save(path)


if __name__ == "__main__":
    os.makedirs(os.path.join(HERE, "..", "build", "tex"), exist_ok=True)
    for b, t in all_textures().items():
        preview(b, t, os.path.join(HERE, "..", "build", "tex", b + ".png"))
        print(b, np.bincount(t[0].ravel(), minlength=8))
