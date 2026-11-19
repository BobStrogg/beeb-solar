"""Generate src/data.6502 for BEEB-SOLAR: maths tables, orbit tables from
JPL's approximate Keplerian elements, the start date's mean anomalies and
mean motions, run-length-coded textures and the body/fact tables."""
import math, sys, os, datetime
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import textures as T

START = datetime.date(2026, 11, 18)          # the date the demo starts on (00:00 UT)
TUNIT = 64                                   # time unit = 1/64 day
ASPECT = 1.1                                 # a sextant pixel is 1.1x wider than tall
out = []
lowout, highout, textout = [], [], []
def emit(s=""): out.append(s)
def to(dst):
    global out
    out = dst
def table(name, vals, w="B", per=16):
    emit(f".{name}")
    vals = [int(v) for v in vals]
    for i in range(0, len(vals), per):
        chunk = vals[i:i + per]
        if w == "B": emit("    EQUB " + ",".join(str(v & 255) for v in chunk))
        else: emit("    EQUW " + ",".join(str(v & 0xFFFF) for v in chunk))
def lohi(name, vals):
    table(name + "_lo", [v & 255 for v in vals]); table(name + "_hi", [(v >> 8) & 255 for v in vals])

to(lowout)
# ------------------------------------------------------------ maths tables
# sextant char from 6 pixel bits: bit5 TL, 4 TR, 3 ML, 2 MR, 1 BL, 0 BR
SEXT = [1, 2, 4, 8, 16, 64]
table("chrtab", [0xA0 | sum(SEXT[5 - b] for b in range(6) if (p >> b) & 1) for p in range(64)])
table("asin_u", [round(math.asin((i + 0.5) / 256) * 128 / (2 * math.pi)) for i in range(256)])
table("sq1", [min(255, round(math.sqrt(max(0, 1 - ((i + 0.5) / 256) ** 2)) * 256)) for i in range(256)])
to(highout); table("vlat", [min(31, max(0, int(32 - math.degrees(math.asin((i + 0.5) / 256)) / 180 * 64))) for i in range(256)]); to(lowout)
rec = [65535] + [min(65535, round(2 ** 18 / i)) for i in range(1, 128)]
to(highout); lohi("recip4", rec); to(lowout)
to(highout); table("ease", [round(255 * (t * t * (3 - 2 * t))) for t in (i / 255 for i in range(256))]); to(lowout)
to(highout); lohi("exp2", [round(256 * 2 ** (i / 64)) for i in range(64)]); to(lowout)
# screen row offsets (cell row * 40) for pixel rows 0..74 and (y mod 3)*2
lohi("rowoff", [(y // 3) * 40 for y in range(75)])
table("ymod", [(y % 3) * 2 for y in range(75)])
table("pyrow", [y // 3 for y in range(75)])
# pixel bit within a sextant char for index (y%3)*2 + (x&1)
table("pixbit", SEXT)

# ------------------------------------------------------------ orbits
EL = {  # a e I L long.peri long.node, and rates per Julian century (JPL, 1800-2050)
 "mercury": ([0.38709927, 0.20563593, 7.00497902, 252.25032350, 77.45779628, 48.33076593],
             [0.00000037, 0.00001906, -0.00594749, 149472.67411175, 0.16047689, -0.12534081]),
 "venus":   ([0.72333566, 0.00677672, 3.39467605, 181.97909950, 131.60246718, 76.67984255],
             [0.00000390, -0.00004107, -0.00078890, 58517.81538729, 0.00268329, -0.27769418]),
 "earth":   ([1.00000261, 0.01671123, -0.00001531, 100.46457166, 102.93768193, 0.0],
             [0.00000562, -0.00004392, -0.01294668, 35999.37244981, 0.32327364, 0.0]),
 "mars":    ([1.52371034, 0.09339410, 1.84969142, -4.55343205, -23.94362959, 49.55953891],
             [0.00001847, 0.00007882, -0.00813131, 19140.30268499, 0.44441088, -0.29257343]),
 "jupiter": ([5.20288700, 0.04838624, 1.30439695, 34.39644051, 14.72847983, 100.47390909],
             [-0.00011607, -0.00013253, -0.00183714, 3034.74612775, 0.21252668, 0.20469106]),
 "saturn":  ([9.53667594, 0.05386179, 2.48599187, 49.95424423, 92.59887831, 113.66242448],
             [-0.00125060, -0.00050991, 0.00193609, 1222.49362201, -0.41897216, -0.28867794]),
 "uranus":  ([19.18916464, 0.04725744, 0.77263783, 313.23810451, 170.95427630, 74.01692503],
             [-0.00196176, -0.00004397, -0.00242939, 428.48202785, 0.40805281, 0.04240589]),
 "neptune": ([30.06992276, 0.00859048, 1.77004347, -55.12002969, 44.96476227, 131.78422574],
             [0.00026291, 0.00005105, 0.00035372, 218.45945325, -0.32241464, -0.00508664]),
}
PLANETS = list(EL)
jd0 = 2451545.0 + (datetime.datetime(START.year, START.month, START.day) - datetime.datetime(2000, 1, 1, 12)).total_seconds() / 86400
Tc = (jd0 - 2451545.0) / 36525

def elements(p):
    e0, r = EL[p]; return [a + b * Tc for a, b in zip(e0, r)]

def helio(p, M):
    a, e, I, L, wb, Om = elements(p)
    w = math.radians(wb - Om); Om = math.radians(Om); I = math.radians(I)
    E = M
    for _ in range(30): E = E - (E - e * math.sin(E) - M) / (1 - e * math.cos(E))
    xp, yp = a * (math.cos(E) - e), a * math.sqrt(1 - e * e) * math.sin(E)
    x = (math.cos(w) * math.cos(Om) - math.sin(w) * math.sin(Om) * math.cos(I)) * xp + (-math.sin(w) * math.cos(Om) - math.cos(w) * math.sin(Om) * math.cos(I)) * yp
    y = (math.cos(w) * math.sin(Om) + math.sin(w) * math.cos(Om) * math.cos(I)) * xp + (-math.sin(w) * math.sin(Om) + math.cos(w) * math.cos(Om) * math.cos(I)) * yp
    return x, y

# whole system: log r mapped piecewise-linearly so the semi-major axes land on
# evenly spaced rings (5, 9, ... 33 pixels)
AX = [EL[p][0][0] for p in EL]
def f_whole(r):
    l = math.log(max(r, 0.2)); k = [math.log(a) for a in AX]
    if l <= k[0]: return 5 + 4 * (l - k[0]) / (k[1] - k[0])
    for i in range(7):
        if l <= k[i + 1] or i == 6: return 5 + 4 * i + 4 * (l - k[i]) / (k[i + 1] - k[i])
def f_inner(r): return r * 18.5

def orbit_table(p, f):
    xs, ys = [], []
    for j in range(64):
        x, y = helio(p, 2 * math.pi * j / 64)
        r = math.hypot(x, y); s = f(r) / r
        xs.append(round(x * s)); ys.append(round(-y * s * ASPECT))
    return xs, ys

whole = [orbit_table(p, f_whole) for p in PLANETS]
inner = [orbit_table(p, f_inner) for p in PLANETS[:4]]
to(highout)
emit("\\ orbit tables: 64 positions per planet at equal steps of mean anomaly, x then y (signed)")
for name, tab in (("orbw", whole), ("orbi", inner)):
    for i, (xs, ys) in enumerate(tab):
        table(f"{name}{i}", xs + ys)
    emit(f".{name}_lo"); emit("    EQUB " + ",".join(f"LO({name}{i})" for i in range(len(tab))))
    emit(f".{name}_hi"); emit("    EQUB " + ",".join(f"HI({name}{i})" for i in range(len(tab))))
to(lowout)
# dot step per planet (every n-th table point is drawn as an orbit dot)
table("dotstep_whole", [4, 4, 2, 2, 1, 1, 1, 1])
table("dotstep_inner", [4, 2, 2, 1])

# mean anomaly at the start date (2^32 per revolution) and mean motion per time unit
M0, N = [], []
for p in PLANETS:
    a, e, I, L, wb, Om = elements(p)
    M0.append(round(((L - wb) % 360) / 360 * 2 ** 32) % 2 ** 32)
    rate = EL[p][1][3] / 36525 / 360                   # rev per day (mean longitude rate)
    N.append(round(rate / TUNIT * 2 ** 32))
# the Moon: mean longitude 218.3164477 + 481267.88123421 deg/century (relative to the ecliptic)
mlon = (218.3164477 + 481267.88123421 * Tc) % 360
M0.append(round(mlon / 360 * 2 ** 32) % 2 ** 32); N.append(round(481267.88123421 / 36525 / 360 / TUNIT * 2 ** 32))
for k in range(4): table(f"m0_{k}", [(v >> (8 * k)) & 255 for v in M0])
for k in range(4): table(f"nrate_{k}", [(v >> (8 * k)) & 255 for v in N])
emit(f"START_YEAR = {START.year}"); emit(f"START_MONTH = {START.month}"); emit(f"START_DAY = {START.day}")

# ------------------------------------------------------------ textures (run-length coded)
def rle(vals):
    o = []; i = 0
    while i < len(vals):
        j = i
        while j < len(vals) and vals[j] == vals[i] and j - i < 32: j += 1
        o.append((vals[i] << 5) | (j - i - 1)); i = j
    return o

texs = T.all_textures()
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
texlen = []
tsize = 0
for b, (m, pal, dith, fg) in texs.items():
    # the base material of a row: the commonest after dithering (a dithered
    # material keeps dith/256 of its texels, the rest become material 0)
    keep = np.array([d / 256 if d else 1.0 for d in dith])
    def commonest(row):
        c = np.bincount(row, minlength=8) * keep
        c[0] += (np.bincount(row, minlength=8) * (1 - keep)).sum()
        return int(c.argmax())
    rowbase = [commonest(m[v]) for v in range(64)]
    if b == "earth":
        rowbase = [3 if T.lat[v] > 76 or T.lat[v] < -70 else 0 for v in range(64)]
    if fg: rowbase = [0] * 64
    data = rle(rowbase) + rle(list(m.ravel()))
    tsize += len(data) + 16; print(b, len(data), file=sys.stderr)
    os.makedirs(os.path.join(ROOT, "build"), exist_ok=True)
    open(os.path.join(ROOT, "build", f"t{T.BODIES.index(b)}.bin"), "wb").write(bytes(data))
    texlen.append(len(data))
    table(f"pal_{b}", pal); table(f"dith_{b}", dith)
emit(f"\\ textures: {tsize} bytes")
print("textures", tsize, "bytes", file=sys.stderr)

# ------------------------------------------------------------ bodies
NAMES = ["SUN", "MERCURY", "VENUS", "EARTH", "MARS", "JUPITER", "SATURN", "URANUS", "NEPTUNE", "MOON"]
TITLECOL = [3, 7, 3, 6, 1, 3, 3, 6, 4, 7]       # alpha colour of the name
DOTCOL = [3, 7, 3, 6, 1, 3, 3, 6, 6, 7]         # system-view dot colour (graphics)
RFULL = [28, 27, 31, 31, 31, 31, 17, 31, 31, 27]
SPIN = [40, 40, -24, 110, 106, 220, 200, -150, 160, 24]   # texels/256 per vsync (visual)
FACTS = [
    ("G2V star  Radius 696,000 km", "Surface 5,500C  Core 15 million C"),
    ("0.39 AU from Sun  Radius 2,440 km", "Day 176 d  Year 88 d  Moons 0"),
    ("0.72 AU from Sun  Radius 6,052 km", "Day 243 d retro  Year 225 d  Moons 0"),
    ("1.00 AU from Sun  Radius 6,371 km", "Day 24 h  Year 365.25 d  Moons 1"),
    ("1.52 AU from Sun  Radius 3,390 km", "Day 24.6 h  Year 687 d  Moons 2"),
    ("5.20 AU from Sun  Radius 69,911 km", "Day 9.9 h  Year 11.9 y  Moons 95"),
    ("9.54 AU from Sun  Radius 58,232 km", "Day 10.7 h  Year 29.5 y  Moons 274"),
    ("19.2 AU from Sun  Radius 25,362 km", "Day 17.2 h retro  Year 84 y  Moons 28"),
    ("30.1 AU from Sun  Radius 24,622 km", "Day 16.1 h  Year 165 y  Moons 16"),
    ("384,400 km from Earth  Radius 1,737 km", "Day 27.3 d  Orbit 27.3 d  Tidal lock"),
]
for s in [n for f in FACTS for n in f]: assert len(s) <= 38, s
lohi("body_texlen", texlen)
emit(".body_pal_lo"); emit("    EQUB " + ",".join(f"LO(pal_{b})" for b in T.BODIES))
emit(".body_pal_hi"); emit("    EQUB " + ",".join(f"HI(pal_{b})" for b in T.BODIES))
table("body_fg", [1 if texs[b][3] else 0 for b in T.BODIES])
table("body_titlecol", TITLECOL); table("body_dotcol", DOTCOL); table("body_rfull", RFULL)
table("body_spin_lo", [s & 255 for s in SPIN]); table("body_spin_hi", [(s >> 8) & 255 for s in SPIN])
# zoom: log2(Rfull / r_sys) * 64 (r_sys = 1 pixel, the Sun 3)
zl = [round(math.log2(RFULL[i] / (3 if i == 0 else 1)) * 64) for i in range(10)]
table("body_zlog", [v & 255 for v in zl]); table("body_zloghi", [v >> 8 for v in zl])
to(textout)                                  # names and facts: file SOLART at &0500
for i, n in enumerate(NAMES):
    emit(f".name{i} EQUS \"{n}\", 0")
for i, (a, b) in enumerate(FACTS):
    emit(f".facta{i} EQUS \"{a}\", 0"); emit(f".factb{i} EQUS \"{b}\", 0")
for t in ("name", "facta", "factb"):
    emit(f".{t}_lo"); emit("    EQUB " + ",".join(f"LO({t}{i})" for i in range(10)))
    emit(f".{t}_hi"); emit("    EQUB " + ",".join(f"HI({t}{i})" for i in range(10)))
to(lowout)

# ------------------------------------------------------------ stars (cell, glyph), avoiding rows 0, 24
g = np.random.default_rng(4)
stars = set()
while len(stars) < 70:
    r, c = int(g.integers(1, 24)), int(g.integers(2, 39))
    stars.add((r, c))
stars = sorted(stars)
lohi("star_off", [r * 40 + c for r, c in stars])
table("star_row", [r for r, c in stars])
table("star_gly", [0xA0 | SEXT[int(g.integers(0, 6))] for _ in stars])
emit(f"NSTARS = {len(stars)}")

open(os.path.join(ROOT, "src", "data.6502"), "w").write("\n".join(lowout) + "\n")
open(os.path.join(ROOT, "src", "datahi.6502"), "w").write("\n".join(highout) + "\n")
open(os.path.join(ROOT, "src", "datatext.6502"), "w").write("\n".join(textout) + "\n")
print("JD0", jd0, "M0", [round(v / 2 ** 32 * 360, 1) for v in M0], file=sys.stderr)
