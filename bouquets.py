"""Four 12-flower bouqet arrangements mixing light green tulips, pink lillies, and white roses."""

import math
import random

from band import build_band_points
from engine import GREENS, PAPER, add, make_leaf_points, norm
from lily import draw_lily
from rose import draw_rose
from tulip import draw_tulip

BOUQUET_SPECS = [
    {
        "id": 1,
        "name": "Classic Trio",
        "subtitle": "4 light green tulips · 4 pink lilies · 4 white roses",
        "types": [
            "lily", "tulip", "rose", "lily",
            "rose", "tulip", "lily", "rose",
            "tulip", "lily", "rose", "tulip",
        ],
        "seed": 21,
    },
    {
        "id": 2,
        "name": "Spring Meadow",
        "subtitle": "6 light green tulips · 3 pink lilies · 3 white roses",
        "types": [
            "tulip", "rose", "tulip", "lily",
            "tulip", "rose", "tulip", "lily",
            "tulip", "rose", "tulip", "lily",
        ],
        "seed": 34,
    },
    {
        "id": 3,
        "name": "Blush & Ivory",
        "subtitle": "6 pink lilies · 4 white roses · 2 light green tulips",
        "types": [
            "lily", "rose", "lily", "tulip",
            "lily", "rose", "lily", "rose",
            "lily", "tulip", "rose", "lily",
        ],
        "seed": 47,
    },
    {
        "id": 4,
        "name": "Ivory Garden",
        "subtitle": "6 white roses · 3 light green tulips · 3 pink lilies",
        "types": [
            "rose", "tulip", "rose", "lily",
            "rose", "tulip", "rose", "lily",
            "rose", "tulip", "rose", "lily",
        ],
        "seed": 58,
    },
]

_DRAW_MAP = {
    "tulip": (draw_tulip, 0.118, 1.18),
    "lily": (draw_lily, 0.134, 1.0),
    "rose": (draw_rose, 0.120, 1.0),
}


def build_bouquet_scene(bouquet_id=1):
    """Build one of the 4 12-flower bouquet scenes matching bouquet3d.py geometry."""
    spec = BOUQUET_SPECS[(bouquet_id - 1) % len(BOUQUET_SPECS)]
    rnd = random.Random(spec["seed"])
    pts = []

    C, D = (0.0, 0.16, 0.0), 0.63
    N = len(spec["types"])
    golden = math.pi * (3 - math.sqrt(5))
    heads = []
    for i in range(N):
        el = math.radians(86 - 52 * math.sqrt(i / (N - 1)))
        az = i * golden
        d = (math.cos(el) * math.cos(az), math.sin(el), math.cos(el) * math.sin(az))
        pos = add(C, d, D * rnd.uniform(0.94, 1.04))
        heads.append((pos, norm(d)))

    neck = (0.0, -0.05, 0.0)
    flowers = []
    for (pos, axis), kind in zip(heads, spec["types"]):
        # Upper stems converge inside the paper cone strictly above the band (by=-0.12).
        base = add(pos, axis, -0.03)
        for j in range(60):
            t = j / 59
            p = (
                base[0] + (neck[0] - base[0]) * t,
                base[1] + (neck[1] - base[1]) * t,
                base[2] + (neck[2] - base[2]) * t,
            )
            pts.append((p[0], p[1], p[2], axis[0], 0.0, axis[2], GREENS, -0.15, True, None))

        draw_fn, radius, y_stretch = _DRAW_MAP[kind]
        flowers.append({
            "kind": kind,
            "pos": pos,
            "axis": axis,
            "radius": radius * rnd.uniform(0.96, 1.04),
            "y_stretch": y_stretch,
            "seed": rnd.uniform(0, 6.28),
            "draw": draw_fn,
        })

    # Eight curled foliage leaves around the wrap rim (exact original geometry)
    for i in range(8):
        a = (i + 0.4) / 8 * 2 * math.pi
        c, s = math.cos(a), math.sin(a)
        pts.extend(make_leaf_points((0.26 * c, 0.30, 0.26 * s), (c, 0.15, s), L=0.30, W=0.07))

    # Paper wrap cone with wavy top rim and 5 vertical folds
    y0, y1, r0, r1 = -0.20, 0.30, 0.06, 0.36
    k = (r1 - r0) / (y1 - y0)
    rings = 55
    for i in range(rings):
        t = i / (rings - 1)
        r = r0 + (r1 - r0) * t
        count = max(14, int(210 * r))
        for j in range(count):
            ph = (j + rnd.random()) / count * 2 * math.pi
            c, s = math.cos(ph), math.sin(ph)
            y = y0 + (y1 - y0) * t
            if t > 0.9:
                y += 0.03 * math.sin(9 * ph)
            fold = 0.3 * (abs(math.sin(5 * ph)) - 0.6)
            nn = norm((c, -k, s))
            pts.append((r * c, y, r * s, nn[0], nn[1], nn[2], PAPER, fold, False, None))

    # Lower stems strictly below the paper wrap (y <= -0.205) so they never intersect the band
    for i in range(7):
        a = i / 7 * 2 * math.pi
        sx, sz = 0.024 * math.cos(a), 0.024 * math.sin(a)
        for j in range(40):
            t = j / 39
            pts.append((
                sx * (1 + 1.15 * t), -0.205 - 0.295 * t, sz * (1 + 1.15 * t),
                math.cos(a), 0.0, math.sin(a), GREENS, -0.1, True, None,
            ))

    # Ocean-blue band and bow holding the wrap together (rotates with the bouquet)
    pts.extend(build_band_points(by=-0.12, y0=y0, y1=y1, r0=r0, r1=r1))

    # Baby's breath filler
    babies = []
    for _ in range(90):
        a = rnd.random() * 2 * math.pi
        el = rnd.uniform(0.3, 1.4)
        rr = rnd.uniform(0.40, 0.58)
        babies.append((
            rr * math.cos(a) * math.cos(el),
            C[1] + rr * math.sin(el),
            rr * math.sin(a) * math.cos(el),
            rnd.uniform(0, 6.28),
        ))

    # Twinkling background sparkles
    sparkles = []
    for _ in range(30):
        a = rnd.random() * 2 * math.pi
        rr = rnd.uniform(0.75, 0.95)
        sparkles.append((
            rr * math.cos(a),
            rnd.uniform(-0.3, 1.0),
            rr * math.sin(a),
            rnd.uniform(0, 6.28),
            rnd.uniform(1.5, 4.0),
        ))

    return spec, (pts, flowers, babies, sparkles)