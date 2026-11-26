"""Pink lily: six pointed petals with deep rose throat and golden stamens."""

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

LILY_PINK = [168, 205, 211, 211, 218, 225]
LILY_THROAT = [125, 161, 168]
LILY_STAMEN = [178, 214, 220, 226]
LILY_CALYX = [28, 34, 71, 77]


def _ang_dist(a, b):
    return abs((a - b + math.pi) % (2 * math.pi) - math.pi)


def draw_lily(plot, fx, fy, zt, rx, ry, dim, rot, view=1.0, side=0.0):
    """Draw a 6-petaled pointed pink lily with golden stamens."""
    squash = 0.64 + 0.36 * abs(view)
    rx_eff = max(2.5, rx * squash)
    up = -math.pi / 2.0 + rot * 0.25
    span = math.pi / 3.0
    back = view < -0.18

    r0 = int(fy - ry) - 1
    r1 = int(fy + ry) + 2
    c0 = int(fx - rx_eff) - 1
    c1 = int(fx + rx_eff) + 2

    for row in range(r0, r1):
        dy = (row + 0.5 - fy) / ry
        for col in range(c0, c1):
            dx = (col + 0.5 - fx) / rx_eff
            s = math.hypot(dx, dy)
            if s > 1.03:
                continue

            ph = math.atan2(dy, dx)

            if back and s < 0.26:
                nearest_c = min(_ang_dist(ph, up + k * span) for k in range(6))
                if s < 0.14 or nearest_c < 0.30:
                    b = min(0.999, max(0.0, 0.45 - 0.20 * dx + dim))
                    plot(col, row, zt + 0.004, "*" if s < 0.13 else "+",
                         LILY_CALYX[int(b * len(LILY_CALYX))])
                    continue

            if not back and 0.06 <= s <= 0.44:
                sx = dx - 0.04 * max(-1.0, min(1.0, side))
                ss = math.hypot(sx, dy)
                sph = math.atan2(dy, sx)
                nearest_st = min(_ang_dist(sph, up + (k + 0.5) * span) for k in range(6))
                if 0.07 <= ss <= 0.42 and ss * nearest_st < 0.038:
                    b = min(0.999, max(0.0, 0.74 - 0.2 * dx + dim * 0.5))
                    if ss > 0.29:
                        plot(col, row, zt + 0.005, "@", LILY_STAMEN[min(len(LILY_STAMEN) - 1, int(b * len(LILY_STAMEN)))])
                    else:
                        plot(col, row, zt + 0.004, "*", LILY_STAMEN[int(b * len(LILY_STAMEN))])
                    continue

            if s < 0.18:
                b = min(0.999, max(0.0, 0.55 - 0.28 * dx - 0.28 * dy + dim))
                plot(col, row, zt + 0.001, "o" if s < 0.10 else "+",
                     LILY_THROAT[int(b * len(LILY_THROAT))])
                continue

            # Slender, sharply separated 6-pointed star lily petals
            nearest = min(_ang_dist(ph, up + k * span) for k in range(6))
            d_perp = s * math.sin(nearest) if nearest < 1.1 else 2.0
            w_perp = 0.185 * math.sin(math.pi * (min(1.0, s) ** 0.72)) + 0.025 * (1.0 - min(1.0, s))
            if nearest > 0.65 or d_perp > w_perp:
                continue

            crease = -0.22 if d_perp < 0.034 and 0.20 < s < 0.78 else 0.0
            edge = -0.14 if d_perp > w_perp * 0.78 or s > 0.88 else 0.0
            b = 0.65 - 0.18 * dx - 0.22 * dy + 0.14 * (d_perp / max(w_perp, 1e-4)) + crease + edge + dim
            b = min(0.999, max(0.0, b))
            plot(
                col,
                row,
                zt + 0.003 * (1.0 - 0.3 * s),
                PETAL_SHADE[int(b * len(PETAL_SHADE))],
                LILY_PINK[int(b * len(LILY_PINK))],
            )


def build_lily_scene():
    """Standalone spinning pink lily with stem and narrow lily leaves."""
    rnd = random.Random(22)
    pts = []
    pos = (0.0, 0.30, 0.0)

    for j in range(60):
        t = j / 59
        y = 0.20 - 0.66 * t
        for k in range(6):
            a = k / 6 * 2 * math.pi
            pts.append((
                0.020 * math.cos(a), y, 0.020 * math.sin(a),
                math.cos(a), 0.0, math.sin(a), GREENS, -0.05, True, None,
            ))

    pts.extend(make_leaf_points((0.02, -0.10, 0.0), (0.75, 0.35, 0.25), L=0.38, W=0.06))
    pts.extend(make_leaf_points((-0.02, -0.20, 0.0), (-0.75, 0.30, -0.20), L=0.36, W=0.06))
    pts.extend(make_leaf_points((0.0, -0.28, 0.02), (0.15, 0.25, 0.80), L=0.34, W=0.055))

    flowers = [{
        "pos": pos,
        "axis": (0.0, 0.35, 0.94),
        "radius": 0.29,
        "y_stretch": 1.0,
        "seed": 0.0,
        "draw": draw_lily,
    }]

    sparkles = [
        (0.46 * math.cos(a), rnd.uniform(-0.2, 0.65), 0.46 * math.sin(a),
         rnd.uniform(0, 6.28), rnd.uniform(1.8, 3.8))
        for a in (i / 14 * 2 * math.pi for i in range(14))
    ]
    return pts, flowers, [], sparkles


if __name__ == "__main__":
    parser = make_argparser("Spinning ASCII pink lily.")
    args = parser.parse_args()
    run_entity(
        build_lily_scene(),
        args,
        preview_stem="lily",
        message="pink lily ♥",
    )