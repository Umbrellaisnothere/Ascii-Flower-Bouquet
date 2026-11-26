"""Shared 3D ASCII rendering engine."""

import argparse
import math
import os
import random
import shutil
import sys
import time
from pathlib import Path

FPS = 24
SPIN_SPEED = 0.6
TILT = 0.30
CAM_DIST = 4.0
PIVOT_Y = 0.2
NUM_HEARTS = 18

SHADE = ".:-=+*%@"
PETAL_SHADE = "+*#%"
RESET = "\033[0m"

GREENS = [22, 28, 28, 34, 35, 71, 77]
PAPER = [101, 144, 180, 187, 223, 230]
HEART_COLORS = [161, 197, 204, 205, 211, 218]
MSG_COLORS = [161, 168, 205, 211, 218, 225, 218, 211, 205, 168]

_L = (-0.45, 0.6, 0.66)
_n = math.sqrt(sum(v * v for v in _L))
LX, LY, LZ = (v / _n for v in _L)


def norm(v):
    m = math.sqrt(v[0] ** 2 + v[1] ** 2 + v[2] ** 2) or 1.0
    return (v[0] / m, v[1] / m, v[2] / m)


def cross(a, b):
    return (
        a[1] * b[2] - a[2] * b[1],
        a[2] * b[0] - a[0] * b[2],
        a[0] * b[1] - a[1] * b[0],
    )


def basis(axis):
    helper = (0.0, 1.0, 0.0) if abs(axis[1]) < 0.9 else (1.0, 0.0, 0.0)
    u = norm(cross(helper, axis))
    return u, cross(axis, u)


def add(p, d, k):
    return (p[0] + d[0] * k, p[1] + d[1] * k, p[2] + d[2] * k)


def make_leaf_points(base, d, L=0.30, W=0.07):
    """Build curled leaf 3D points matching the original bouquet3d.py geometry."""
    d = norm(d)
    side = norm((-d[2], 0.0, d[0])) if (d[0] != 0.0 or d[2] != 0.0) else (1.0, 0.0, 0.0)
    n = norm(cross(side, d))
    pts = []
    for ti in range(32):
        t = ti / 31
        for wi in range(-5, 6):
            w = wi / 5
            curl = 0.025 * w * w
            p = (
                base[0] + d[0] * L * t + side[0] * W * math.sin(math.pi * t) * w + n[0] * curl,
                base[1] + d[1] * L * t - 0.10 * t * t + n[1] * curl,
                base[2] + d[2] * L * t + side[2] * W * math.sin(math.pi * t) * w + n[2] * curl,
            )
            rib = -0.25 if wi == 0 else 0.0
            pts.append((p[0], p[1], p[2], n[0], n[1], n[2], GREENS, rib, True, None))
    return pts


def compute_scene_bounds(scene, tilt=TILT, cam_dist=CAM_DIST, pivot_y=PIVOT_Y):
    """Measure projected extents over a full 360-degree spin so nothing is cropped."""
    pts, flowers, babies, sparkles = scene
    ct, st = math.cos(tilt), math.sin(tilt)
    yt_max = -1e9
    yt_min = 1e9
    xr_max = 0.2

    for step in range(24):
        ang = step / 24 * 2 * math.pi
        ca, sa = math.cos(ang), math.sin(ang)

        for p in pts:
            x, y, z = p[0], p[1], p[2]
            xr = x * ca - z * sa
            zr = x * sa + z * ca
            yp = y - pivot_y
            yt = yp * ct - zr * st
            zt = yp * st + zr * ct
            f = cam_dist / max(0.4, cam_dist - zt)
            yt_max = max(yt_max, yt * f)
            yt_min = min(yt_min, yt * f)
            xr_max = max(xr_max, abs(xr * f))

        for fl in flowers:
            x, y, z = fl["pos"]
            r = fl["radius"]
            ys = fl.get("y_stretch", 1.0)
            xr = x * ca - z * sa
            zr = x * sa + z * ca
            yp = y - pivot_y
            yt = yp * ct - zr * st
            zt = yp * st + zr * ct
            f = cam_dist / max(0.4, cam_dist - zt)
            yt_max = max(yt_max, (yt + r * ys * 1.08) * f)
            yt_min = min(yt_min, (yt - r * ys * 1.08) * f)
            xr_max = max(xr_max, (abs(xr) + r * 1.08) * f)

    return yt_min, yt_max, xr_max


def update_hearts(hearts, dt):
    while len(hearts) < NUM_HEARTS:
        hearts.append([
            random.random(),
            1.0 + random.random(),
            random.uniform(0.03, 0.08),
            random.uniform(0, 6.28),
            random.choice(HEART_COLORS),
        ])
    for h in hearts:
        h[1] -= h[2] * dt
        if h[1] < 0:
            h[0], h[1], h[4] = random.random(), 1.0, random.choice(HEART_COLORS)


def render_grid(
    scene,
    t,
    cols,
    rows,
    hearts,
    message="for you ♥",
    hint="Ctrl+C to stop",
    bounds=None,
    tilt=TILT,
    cam_dist=CAM_DIST,
    pivot_y=PIVOT_Y,
    spin_speed=SPIN_SPEED,
):
    pts, flowers, babies, sparkles = scene
    chars = [[" "] * cols for _ in range(rows)]
    colors = [[0] * cols for _ in range(rows)]
    zbuf = [[-1e9] * cols for _ in range(rows)]

    view_rows = rows - 2
    if bounds is None:
        bounds = compute_scene_bounds(scene, tilt=tilt, cam_dist=cam_dist, pivot_y=pivot_y)
    yt_min, yt_max, xr_max = bounds
    span_y = max(0.4, yt_max - yt_min)
    span_x = max(0.3, xr_max * 2.0)

    scale = max(1.0, min((view_rows - 3.0) / span_y, (cols - 4.0) / (span_x * 1.05)))
    sx_scale = scale * 2.0
    cx = cols / 2
    cy = 1.5 + yt_max * scale + max(0.0, (view_rows - 3.0 - span_y * scale) * 0.45)

    ang = t * spin_speed
    ca, sa = math.cos(ang), math.sin(ang)
    ct, st = math.cos(tilt), math.sin(tilt)

    def project(x, y, z):
        xr = x * ca - z * sa
        zr = x * sa + z * ca
        yp = y - pivot_y
        yt = yp * ct - zr * st
        zt = yp * st + zr * ct
        f = cam_dist / (cam_dist - zt)
        return int(cx + xr * f * sx_scale), int(cy - yt * f * scale), zt

    def project_f(x, y, z):
        xr = x * ca - z * sa
        zr = x * sa + z * ca
        yp = y - pivot_y
        yt = yp * ct - zr * st
        zt = yp * st + zr * ct
        f = cam_dist / (cam_dist - zt)
        return cx + xr * f * sx_scale, cy - yt * f * scale, zt, f

    def plot(col, row, z, ch, color):
        if 0 <= row < view_rows and 0 <= col < cols and z > zbuf[row][col]:
            zbuf[row][col] = z
            chars[row][col] = ch
            colors[row][col] = color

    for x, y, _, phase, color in hearts:
        col = int((x + 0.015 * math.sin(t * 1.2 + phase)) * cols) % cols
        plot(col, int(y * view_rows), -50, "♥", color)

    for x, y, z, nx, ny, nz, pal, tone, two_sided, override in pts:
        col, row, zt = project(x, y, z)
        nxr = nx * ca - nz * sa
        nzr = nx * sa + nz * ca
        nyt = ny * ct - nzr * st
        nzt = ny * st + nzr * ct
        dot = nxr * LX + nyt * LY + nzt * LZ
        if two_sided and dot < 0:
            dot = -dot * 0.55
        b = 0.25 + 0.75 * max(0.0, dot) + tone
        b = min(0.999, max(0.0, b))
        if override == "P":
            ch = PETAL_SHADE[int(b * len(PETAL_SHADE))]
        else:
            ch = override or SHADE[int(b * len(SHADE))]
        plot(col, row, zt, ch, pal[int(b * len(pal))])

    for fl in flowers:
        x, y, z = fl["pos"]
        ax = fl.get("axis", (0.0, 0.3, 0.95))
        R = fl["radius"]
        y_stretch = fl.get("y_stretch", 1.0)
        seed = fl.get("seed", 0.0)
        draw_fn = fl["draw"]

        fx, fy, zt, f = project_f(x, y, z)
        rx = R * f * sx_scale
        ry = R * y_stretch * f * scale
        dim = -0.4 * (1 - min(1.0, max(0.0, (zt + 0.6) / 1.2)))
        rot = seed + ang * 0.7

        ax_xr = ax[0] * ca - ax[2] * sa
        ax_zr = ax[0] * sa + ax[2] * ca
        ax_zt = ax[1] * st + ax_zr * ct
        view = ax_zt
        side = ax_xr

        draw_fn(plot, fx, fy, zt, rx, ry, dim, rot, view=view, side=side)

    for x, y, z, phase in babies:
        col, row, zt = project(x, y, z)
        star = math.sin(t * 2 + phase) > 0.6
        plot(col, row, zt + 0.02, "*" if star else "·", 231 if star else 255)

    for x, y, z, phase, speed in sparkles:
        col, row, zt = project(x, y, z)
        tw = math.sin(t * speed + phase)
        if tw > 0.85:
            plot(col, row, zt, "*", 231)
        elif tw > 0.4:
            plot(col, row, zt, "+", 225)
        elif tw > 0.0:
            plot(col, row, zt, "·", 218)

    mrow = rows - 2
    start = max(0, (cols - len(message)) // 2)
    shift = int(t * 6)
    for i, ch in enumerate(message):
        if start + i < cols:
            chars[mrow][start + i] = ch
            colors[mrow][start + i] = MSG_COLORS[(i + shift) % len(MSG_COLORS)]

    if hint:
        hstart = max(0, (cols - len(hint)) // 2)
        for i, ch in enumerate(hint):
            if hstart + i < cols:
                chars[rows - 1][hstart + i] = ch
                colors[rows - 1][hstart + i] = 242

    return chars, colors


def grid_to_ansi(chars, colors):
    lines = []
    for rc, rcol in zip(chars, colors):
        last = -1
        parts = []
        for ch, col_code in zip(rc, rcol):
            if ch != " " and col_code != last:
                last = col_code
                parts.append(f"\033[38;5;{last}m")
            parts.append(ch)
        lines.append("".join(parts))
    return "\033[H" + "\n".join(lines) + RESET


def grid_to_plain(chars):
    return "\n".join("".join(row).rstrip() for row in chars)


def render(scene, t, cols, rows, hearts, **kwargs):
    chars, colors = render_grid(scene, t, cols, rows, hearts, **kwargs)
    return grid_to_ansi(chars, colors)


def xterm256_to_rgb(c):
    if c < 16:
        base = [
            (0, 0, 0), (128, 0, 0), (0, 128, 0), (128, 128, 0),
            (0, 0, 128), (128, 0, 128), (0, 128, 128), (192, 192, 192),
            (128, 128, 128), (255, 0, 0), (0, 255, 0), (255, 255, 0),
            (0, 0, 255), (255, 0, 255), (0, 255, 255), (255, 255, 255),
        ]
        return base[c]
    if c < 232:
        c -= 16
        r, g, b = c // 36, (c // 6) % 6, c % 6
        lut = [0, 95, 135, 175, 215, 255]
        return (lut[r], lut[g], lut[b])
    v = 8 + (c - 232) * 10
    return (v, v, v)


def _find_mono_font(size):
    from PIL import ImageFont

    candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationMono-Regular.ttf",
    ]
    for path in candidates:
        if os.path.exists(path):
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def grid_to_image(chars, colors, font_size=14, bg=(26, 28, 35)):
    """Render a terminal grid to a Pillow Image (used only for --preview)."""
    from PIL import Image, ImageDraw

    font = _find_mono_font(font_size)
    probe = Image.new("RGB", (1, 1))
    dprobe = ImageDraw.Draw(probe)
    bbox = dprobe.textbbox((0, 0), "M", font=font)
    cw = max(6, bbox[2] - bbox[0] + 1)
    ch = max(10, int(font_size * 1.28))

    rows = len(chars)
    cols = len(chars[0]) if rows else 0
    pad = 16
    img = Image.new("RGB", (cols * cw + 2 * pad, rows * ch + 2 * pad), bg)
    draw = ImageDraw.Draw(img)

    for r in range(rows):
        y = pad + r * ch
        for c in range(cols):
            glyph = chars[r][c]
            if glyph != " ":
                rgb = xterm256_to_rgb(colors[r][c])
                draw.text((pad + c * cw, y), glyph, font=font, fill=rgb)
    return img


def make_argparser(description):
    p = argparse.ArgumentParser(description=description)
    p.add_argument("--frames", type=int, default=0, help="Print N plain-text frames and exit.")
    p.add_argument("--cols", type=int, default=0, help="Terminal width in columns.")
    p.add_argument("--rows", type=int, default=0, help="Terminal height in rows.")
    p.add_argument("--speed", type=float, default=SPIN_SPEED, help="Spin speed in rad/s.")
    p.add_argument("--save-frames", type=Path, metavar="DIR", help="Save plain-text frames to DIR.")
    p.add_argument("--preview", action="store_true", help="Write PNG (and GIF if spinning) preview.")
    p.add_argument("--preview-dir", type=Path, default=Path("previews"), help="Output directory for previews.")
    p.add_argument("--name", default="", help="Override preview file stem.")
    return p


def seeded_hearts(seed=7):
    rnd = random.Random(seed)
    return [
        [rnd.random(), rnd.uniform(0.05, 0.95), rnd.uniform(0.03, 0.08),
         rnd.uniform(0, 6.28), rnd.choice(HEART_COLORS)]
        for _ in range(NUM_HEARTS)
    ]


def run_entity(
    scene,
    args,
    preview_stem,
    message="for you ♥",
    hint="Ctrl+C to stop",
    still_t=0.4,
    n_gif=28,
    gif=True,
):
    bounds = compute_scene_bounds(scene)

    if args.frames or args.save_frames or args.preview:
        cols = args.cols or 100
        rows = args.rows or 44
        hearts = seeded_hearts()
        if args.save_frames:
            args.save_frames.mkdir(parents=True, exist_ok=True)
        n = args.frames or (4 if args.save_frames else 0)
        for i in range(n):
            t = i * (2 * math.pi / max(args.speed, 1e-6)) / max(n, 1)
            chars, colors = render_grid(
                scene, t, cols, rows, hearts,
                message=message, hint=hint, bounds=bounds, spin_speed=args.speed,
            )
            plain = grid_to_plain(chars)
            if args.save_frames:
                (args.save_frames / f"{preview_stem}_frame_{i:02d}.txt").write_text(
                    plain + "\n", encoding="utf-8"
                )
            else:
                if i:
                    print("\n" + "-" * min(cols, 72) + "\n")
                print(plain)

        if args.preview:
            args.preview_dir.mkdir(parents=True, exist_ok=True)
            stem = args.name or preview_stem
            chars, colors = render_grid(
                scene, still_t, cols, rows, hearts,
                message=message, hint=hint, bounds=bounds, spin_speed=args.speed,
            )
            png_path = args.preview_dir / f"{stem}.png"
            grid_to_image(chars, colors, font_size=14).save(png_path, "PNG")
            print(f"Saved {png_path}")
            if gif:
                imgs = []
                for i in range(n_gif):
                    t = i * (2 * math.pi / max(args.speed, 1e-6)) / n_gif
                    h = seeded_hearts()
                    update_hearts(h, t)
                    c_g, col_g = render_grid(
                        scene, t, cols, rows, h,
                        message=message, hint=hint, bounds=bounds, spin_speed=args.speed,
                    )
                    imgs.append(grid_to_image(c_g, col_g, font_size=11))
                gif_path = args.preview_dir / f"{stem}.gif"
                imgs[0].save(
                    gif_path,
                    save_all=True,
                    append_images=imgs[1:],
                    duration=int(1000 / 12),
                    loop=0,
                )
                print(f"Saved {gif_path}")
        return

    if os.name == "nt":
        os.system("")
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

    hearts = []
    sys.stdout.write("\033[?25l\033[2J")
    start = last = time.perf_counter()
    last_size = None
    try:
        while True:
            now = time.perf_counter()
            dt, last = now - last, now
            size = shutil.get_terminal_size((80, 30))
            cols = args.cols or max(20, size.columns - 1)
            rows = args.rows or max(12, size.lines - 1)
            if (cols, rows) != last_size:
                sys.stdout.write("\033[2J")
                last_size = (cols, rows)
            update_hearts(hearts, dt)
            sys.stdout.write(
                render(
                    scene, now - start, cols, rows, hearts,
                    message=message, hint=hint, bounds=bounds, spin_speed=args.speed,
                )
            )
            sys.stdout.flush()
            wait = 1 / FPS - (time.perf_counter() - now)
            if wait > 0:
                time.sleep(wait)
    except KeyboardInterrupt:
        pass
    finally:
        sys.stdout.write(RESET + "\033[?25h\033[2J\033[H")
        print("\033[38;5;205m♥\033[0m")