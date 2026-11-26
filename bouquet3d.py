"""Spinning 3D ASCII Flower Bouquet

This combines light green tulips, pink lilies, and white roses into 4 selectable or cycling bouquets, held together by an ocean-blue ribbon band and bow.
"""
import math
import os
import random
import shutil
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from bouquets import BOUQUET_SPECS, build_bouquet_scene  # noqa: E402
from engine import (  # noqa: E402
    FPS,
    RESET,
    SPIN_SPEED,
    compute_scene_bounds,
    grid_to_image,
    grid_to_plain,
    make_argparser,
    render,
    render_grid,
    seeded_hearts,
    update_hearts,
)

MESSAGE = "for you ♥"

def _run_bouquet_live(args):
    if os.name == "nt":
        os.system("")
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

    scenes = [build_bouquet_scene(spec["id"]) for spec in BOUQUET_SPECS]
    bounds_list = [compute_scene_bounds(sc) for _, sc in scenes]
    turn_sec = 2 * math.pi / max(args.speed, 1e-6)
    hearts = []

    sys.stdout.write("\033[?25l\033[2J")
    start = last = time.perf_counter()
    last_size = None
    try:
        while True:
            now = time.perf_counter()
            elapsed = now - start
            dt, last = now - last, now
            size = shutil.get_terminal_size((80, 30))
            cols = args.cols or max(20, size.columns - 1)
            rows = args.rows or max(12, size.lines - 1)
            if (cols, rows) != last_size:
                sys.stdout.write("\033[2J")
                last_size = (cols, rows)

            if args.cycle:
                idx = int(elapsed // turn_sec) % len(scenes)
            else:
                idx = (args.bouquet - 1) % len(scenes)
            spec, scene = scenes[idx]
            bounds = bounds_list[idx]

            update_hearts(hearts, dt)
            msg = args.message or f"{spec['name']} ♥"
            hint = f"[{spec['id']}/4] {spec['subtitle']} | --bouquet 1..4 / --cycle"
            sys.stdout.write(
                render(
                    scene,
                    elapsed,
                    cols,
                    rows,
                    hearts,
                    message=msg,
                    hint=hint,
                    bounds=bounds,
                    spin_speed=args.speed,
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


def _export_outputs(args):
    cols = args.cols or 116
    rows = args.rows or 52
    ids = [s["id"] for s in BOUQUET_SPECS] if args.all_previews else [args.bouquet]

    for bid in ids:
        spec, scene = build_bouquet_scene(bid)
        bounds = compute_scene_bounds(scene)
        msg = args.message or f"{spec['name']} ♥"
        hint = f"[{spec['id']}/4] {spec['subtitle']}"
        stem = args.name or f"bouquet_{spec['id']}"
        hearts = seeded_hearts(seed=10 + bid)

        n = args.frames or (4 if args.save_frames and bid == ids[0] else 0)
        if n:
            if args.save_frames:
                args.save_frames.mkdir(parents=True, exist_ok=True)
            for i in range(n):
                t = i * (2 * math.pi / max(args.speed, 1e-6)) / max(n, 1)
                chars, colors = render_grid(
                    scene, t, cols, rows, hearts,
                    message=msg, hint=hint, bounds=bounds, spin_speed=args.speed,
                )
                plain = grid_to_plain(chars)
                if args.save_frames:
                    out_txt = args.save_frames / f"{stem}_frame_{i:02d}.txt"
                    out_txt.write_text(plain + "\n", encoding="utf-8")
                else:
                    if i:
                        print("\n" + "-" * min(cols, 72) + "\n")
                    print(plain)

        if args.preview or args.all_previews:
            args.preview_dir.mkdir(parents=True, exist_ok=True)
            # Still frame facing front-ish (t=0.25 -> ~8.6 deg) so bow + dome read clearly
            chars, colors = render_grid(
                scene, 0.25, cols, rows, hearts,
                message=msg, hint=hint, bounds=bounds, spin_speed=args.speed,
            )
            png_path = args.preview_dir / f"{stem}.png"
            grid_to_image(chars, colors, font_size=14).save(png_path, "PNG")
            print(f"Saved {png_path}")

            if bid == ids[0]:
                imgs = []
                n_gif = 30
                for i in range(n_gif):
                    t = i * (2 * math.pi / max(args.speed, 1e-6)) / n_gif
                    h = seeded_hearts(seed=10 + bid)
                    update_hearts(h, t)
                    c_g, col_g = render_grid(
                        scene, t, cols, rows, h,
                        message=msg, hint=hint, bounds=bounds, spin_speed=args.speed,
                    )
                    imgs.append(grid_to_image(c_g, col_g, font_size=11))
                gif_name = "bouquet_spin.gif" if args.all_previews else f"{stem}.gif"
                gif_path = args.preview_dir / gif_name
                imgs[0].save(
                    gif_path,
                    save_all=True,
                    append_images=imgs[1:],
                    duration=int(1000 / 12),
                    loop=0,
                )
                print(f"Saved {gif_path}")


def main():
    parser = make_argparser("Spinning 3D ASCII flower bouquet.")
    parser.add_argument(
        "--bouquet", type=int, default=1, choices=[1, 2, 3, 4],
        help="Bouquet arrangement 1..4 (default: 1).",
    )
    parser.add_argument(
        "--cycle", action="store_true",
        help="Cycle through all 4 bouquets on each full rotation.",
    )
    parser.add_argument(
        "--all-previews", action="store_true",
        help="Render PNG previews for all 4 bouquets and a spin GIF.",
    )
    parser.add_argument(
        "--message", default="",
        help="Custom message displayed beneath the bouquet.",
    )
    args = parser.parse_args()

    if args.frames or args.save_frames or args.preview or args.all_previews:
        _export_outputs(args)
    else:
        _run_bouquet_live(args)


if __name__ == "__main__":
    main()