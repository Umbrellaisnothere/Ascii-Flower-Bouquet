"""Light green tulip: cup silhouette with three pointed lips."""

import math
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from engine import (  # noqa: E402
    GREENS,
    PETAL_SHADE,
    make_argparser,
    make_leaf_points,
    run_entity,
)

# Bright pastel spring/mint green palette, clearly lighter than stem/leaf GREENS.
TULIP_GREEN = [114, 120, 156, 157, 193, 194]
TULIP_THROAT = [142, 184, 228]
TULIP_CALYX = [28, 34, 71, 77]


def draw_tulip(plot, fx, fy, zt, rx, ry, dim, rot, view=1.0, side=0.0):
    """Draw a light green tulip cup with three pointed lips."""
    shift = 0.08 * max(-1.0, min(1.0, side))
    peaks = (-0.47 + shift, 0.0 + shift * 0.4, 0.47 + shift)
    half_w = 0.275
    v_rim = 0.63

    r0 = int(fy - ry) - 1
    r1 = int(fy + ry) + 2
    c0 = int(fx - rx) - 1
    c1 = int(fx + rx) + 2

    for row in range(r0, r1):
        dy = (row + 0.5 - fy) / ry
        v = (1.0 - dy) / 2.0  # 0 = cup base, 1 = pointed tips
        if v < 0.0 or v > 1.02:
            continue

        grow = math.sin(math.pi * 0.5 * min(1.0, v / 0.55))
        hw = 0.16 + 0.59 * (grow ** 0.80)
        if v > v_rim - 0.04:
            hw = max(hw, 0.74)

        for col in range(c0, c1):
            dx = (col + 0.5 - fx) / rx
            if abs(dx) > hw:
                continue

            lip = 0.0
            for pk in peaks:
                u = abs(dx - pk) / half_w
                if u < 1.0:
                    lip = max(lip, (1.0 - u) ** 1.18)

            v_top = v_rim + 0.37 * lip
            if v > v_top:
                continue

            xn = dx / hw

            # Inner throat only inside the two V-notches between the three lips.
            if abs(dx) < 0.38 and v > v_rim - 0.02 and lip < 0.16 and view > -0.25:
                b = min(0.999, max(0.0, 0.52 + 0.20 * v + dim))
                plot(col, row, zt + 0.001, "o" if v < v_rim + 0.05 else "+",
                     TULIP_THROAT[int(b * len(TULIP_THROAT))])
                continue

            # Green calyx base hugging the bottom of the cup.
            if v < 0.09:
                b = min(0.999, max(0.0, 0.45 - 0.25 * xn + dim))
                plot(col, row, zt + 0.002, "*", TULIP_CALYX[int(b * len(TULIP_CALYX))])
                continue

            seam = -0.24 if (abs(abs(xn) - 0.34) < 0.10 and 0.18 < v < 0.88) else 0.0
            edge = -0.14 if (abs(abs(dx) - hw) < 0.06 or (v_top - v) < 0.05) else 0.0
            b = 0.62 - 0.22 * xn + 0.14 * v + seam + edge + dim * 0.85
            b = min(0.999, max(0.0, b))
            plot(
                col,
                row,
                zt + 0.003,
                PETAL_SHADE[int(b * len(PETAL_SHADE))],
                TULIP_GREEN[int(b * len(TULIP_GREEN))],
            )


def build_tulip_scene():
    """Standalone spinning light green tulip with stem and two tulip leaves."""
    rnd = random.Random(11)
    pts = []
    pos = (0.0, 0.32, 0.0)

    for j in range(60):
        t = j / 59
        y = 0.20 - 0.66 * t
        for k in range(6):
            a = k / 6 * 2 * math.pi
            pts.append((
                0.022 * math.cos(a), y, 0.022 * math.sin(a),
                math.cos(a), 0.0, math.sin(a), GREENS, -0.05, True, None,
            ))

    pts.extend(make_leaf_points((0.02, -0.18, 0.0), (0.55, 0.65, 0.20), L=0.46, W=0.095))
    pts.extend(make_leaf_points((-0.02, -0.26, 0.0), (-0.52, 0.58, -0.25), L=0.44, W=0.095))

    flowers = [{
        "pos": pos,
        "axis": (0.0, 0.35, 0.94),
        "radius": 0.26,
        "y_stretch": 1.18,
        "seed": 0.0,
        "draw": draw_tulip,
    }]

    sparkles = [
        (0.45 * math.cos(a), rnd.uniform(-0.2, 0.65), 0.45 * math.sin(a),
         rnd.uniform(0, 6.28), rnd.uniform(1.8, 3.8))
        for a in (i / 14 * 2 * math.pi for i in range(14))
    ]
    return pts, flowers, [], sparkles


if __name__ == "__main__":
    parser = make_argparser("Spinning ASCII light green tulip.")
    args = parser.parse_args()
    run_entity(
        build_tulip_scene(),
        args,
        preview_stem="tulip",
        message="light green tulip ♥",
    )