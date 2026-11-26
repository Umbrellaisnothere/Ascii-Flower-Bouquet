"""Ocean-blue band and ribbon bow: holds the bouquet wrap and spins with it."""

import math
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from engine import (  # noqa: E402
    make_argparser,
    run_entity,
)

OCEAN_BLUE = [18, 24, 31, 38, 39, 45, 81]


def build_band_points(by=-0.12, y0=-0.20, y1=0.30, r0=0.06, r1=0.36):
    """Build 3D points for the ocean-blue collar band, knot, bow loops, and tails."""
    pts = []
    k = (r1 - r0) / (y1 - y0)
    br = r0 + k * (by - y0) + 0.012

    for j in range(200):
        ph = j / 200 * 2 * math.pi
        c, s = math.cos(ph), math.sin(ph)
        for dy in (-0.020, -0.012, -0.004, 0.004, 0.012, 0.020):
            tone = 0.08 if abs(dy) < 0.006 else -0.04
            pts.append((
                br * c, by + dy, br * s,
                c, 0.0, s,
                OCEAN_BLUE, tone, False, None,
            ))

    knot = (0.0, by, br + 0.012)
    for side in (-1, 1):
        for j in range(110):
            a = j / 110 * 2 * math.pi
            lx = side * (0.072 + 0.072 * math.cos(a))
            ly = 0.044 * math.sin(a) + 0.022 * (0.072 + 0.072 * math.cos(a)) / 0.144
            for fill in (1.0, 0.82, 0.62, 0.42, 0.24):
                tone = 0.14 if fill > 0.85 else 0.04
                pts.append((
                    knot[0] + lx * fill,
                    knot[1] + ly * fill,
                    knot[2] + 0.012 + 0.008 * math.sin(a),
                    side * 0.28, 0.22, 0.93,
                    OCEAN_BLUE, tone, True, None,
                ))

        for j in range(48):
            t = j / 47
            for w in (-0.008, 0.0, 0.008):
                pts.append((
                    knot[0] + side * (0.018 + 0.062 * t) + w,
                    knot[1] - 0.165 * t,
                    knot[2] + 0.016 - 0.012 * t,
                    side * 0.2, 0.0, 0.98,
                    OCEAN_BLUE, -0.04 + 0.06 * math.sin(t * 9), True, None,
                ))

    for dx in (-0.014, -0.007, 0.0, 0.007, 0.014):
        for dy in (-0.010, 0.0, 0.010):
            pts.append((
                dx, by + dy, knot[2] + 0.024,
                0.0, 0.0, 1.0,
                OCEAN_BLUE, 0.22, True, "@",
            ))

    return pts


def build_band_scene():
    """Standalone spinning ocean-blue band and bow."""
    rnd = random.Random(44)
    raw = build_band_points(by=0.18, y0=0.10, y1=0.60, r0=0.11, r1=0.41)
    pts = []
    for p in raw:
        pts.append((p[0] * 1.9, (p[1] - 0.14) * 1.9 + 0.18, p[2] * 1.9, *p[3:]))

    sparkles = [
        (0.45 * math.cos(a), rnd.uniform(-0.15, 0.45), 0.45 * math.sin(a),
         rnd.uniform(0, 6.28), rnd.uniform(1.8, 3.8))
        for a in (i / 14 * 2 * math.pi for i in range(14))
    ]
    return pts, [], [], sparkles


if __name__ == "__main__":
    parser = make_argparser("Spinning ASCII ocean-blue band and bow.")
    args = parser.parse_args()
    run_entity(
        build_band_scene(),
        args,
        preview_stem="band",
        message="ocean-blue band & bow ♥",
    )