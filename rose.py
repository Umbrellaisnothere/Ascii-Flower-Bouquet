"""White rose: layered spiral petals with warm cream heart and green sepals."""

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

# Bright white petals with subtle alabaster grooves so spiral reads in full 360 spin.
WHITE_ROSE = [250, 252, 254, 255, 255, 231]
ROSE_CREAM = [223, 229, 230, 231]
ROSE_SEPAL = [28, 34, 71, 77]


def draw_rose(plot, fx, fy, zt, rx, ry, dim, rot, view=1.0, side=0.0):
    """Draw a white rose with readable spiral petal layers and green sepals."""
    squash = 0.70 + 0.30 * abs(view)
    rx_eff = max(2.5, rx * squash)
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
            if s > 1.05:
                continue

            ph = math.atan2(dy, dx) + rot * 0.55

            scallop = 0.5 + 0.5 * math.cos(5.0 * ph)
            reach = 0.84 + 0.16 * (scallop ** 0.72)

            if back and s < 0.40:
                sep_ang = abs((math.atan2(dy, dx) - (-math.pi / 2.0)) % (2 * math.pi / 5) - math.pi / 5)
                if s < 0.18 or sep_ang < 0.28:
                    b = min(0.999, max(0.0, 0.45 - 0.20 * dx + dim))
                    plot(col, row, zt + 0.004, "*" if s < 0.18 else "+",
                         ROSE_SEPAL[int(b * len(ROSE_SEPAL))])
                    continue

            if not back and 0.72 < dy < 1.00 and abs(dx) < 0.48:
                for pk, hw in ((-0.30, 0.18), (0.0, 0.16), (0.30, 0.18)):
                    u = abs(dx - pk) / hw
                    if u < 1.0 and dy < 0.76 + 0.22 * ((1.0 - u) ** 1.3):
                        b = min(0.999, max(0.0, 0.50 - 0.18 * dx + dim))
                        plot(col, row, zt + 0.001, "*", ROSE_SEPAL[int(b * len(ROSE_SEPAL))])
                        break

            if s > reach:
                continue

            if s < 0.23 and not back:
                swirl = 0.5 + 0.5 * math.sin(2.0 * ph - 11.0 * s)
                b = min(0.999, max(0.0, 0.45 + 0.42 * swirl - 0.12 * dx - 0.14 * dy + dim * 0.7))
                plot(
                    col,
                    row,
                    zt + 0.004,
                    "@" if s < 0.10 else ("o" if swirl < 0.45 else "#"),
                    ROSE_CREAM[int(b * len(ROSE_CREAM))],
                )
                continue

            # Crisp 2.2-turn spiral whorls that stay bright white with dark petal tuck grooves
            s_waved = s + 0.045 * math.sin(5.0 * ph + 3.0 * s)
            layer = (s_waved * 2.25 - ph / (2.0 * math.pi)) % 1.0
            if layer < 0.22:
                fold = -0.45
            elif layer > 0.70:
                fold = 0.26
            else:
                fold = 0.10 * (layer - 0.45)

            edge = -0.14 if s > reach - 0.08 else 0.0
            b = 0.68 - 0.10 * dx - 0.14 * dy + fold + edge + dim * 0.7
            b = min(0.999, max(0.0, b))
            plot(
                col,
                row,
                zt + 0.003 * (1.0 - 0.25 * s),
                PETAL_SHADE[int(b * len(PETAL_SHADE))],
                WHITE_ROSE[int(b * len(WHITE_ROSE))],
            )


def build_rose_scene():
    """Standalone spinning white rose with stem and leaves."""
    rnd = random.Random(33)
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

    pts.extend(make_leaf_points((0.02, -0.12, 0.0), (0.70, 0.30, 0.25), L=0.35, W=0.075))
    pts.extend(make_leaf_points((-0.02, -0.22, 0.0), (-0.68, 0.25, -0.20), L=0.34, W=0.075))

    flowers = [{
        "pos": pos,
        "axis": (0.0, 0.35, 0.94),
        "radius": 0.26,
        "y_stretch": 1.0,
        "seed": 0.4,
        "draw": draw_rose,
    }]

    sparkles = [
        (0.45 * math.cos(a), rnd.uniform(-0.2, 0.65), 0.45 * math.sin(a),
         rnd.uniform(0, 6.28), rnd.uniform(1.8, 3.8))
        for a in (i / 14 * 2 * math.pi for i in range(14))
    ]
    return pts, flowers, [], sparkles


if __name__ == "__main__":
    parser = make_argparser("Spinning ASCII white rose.")
    args = parser.parse_args()
    run_entity(
        build_rose_scene(),
        args,
        preview_stem="rose",
        message="white rose ♥",
    )