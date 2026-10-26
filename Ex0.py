"""Demo: cut a 3D volume along a list of planes and save the cuts as a video.

Usage:
    python Ex0.py <file.nrrd> <file.csv> <file.mp4> [--fps 10] [--png-dir DIR]

    file.nrrd  the 3D volume
    file.csv   one plane per line: 9 numbers (a, b, c) or 12 (a1, a2, b, c)
    file.mp4   the output video, one frame per plane, in CSV order
"""
from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

from projection import Projector
from projection.io import check_output_path, intensity_window, load_volume, read_planes, to_uint8, write_video


def _positive_int(text: str) -> int:
    try:
        value = int(text)
    except ValueError:
        raise argparse.ArgumentTypeError(f"must be a positive whole number, got {text}") from None
    if value <= 0:
        raise argparse.ArgumentTypeError(f"must be a positive whole number, got {text}")
    return value


def _fail(message: str) -> int:
    print(f"error: {message}", file=sys.stderr)
    return 2


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("nrrd", help="3D volume (NRRD)")
    parser.add_argument("csv", help="list of planes (CSV)")
    parser.add_argument("mp4", help="output video (MP4)")
    parser.add_argument("--fps", type=_positive_int, default=10, help="frames per second in the video (default 10)")
    parser.add_argument("--png-dir", help="also save every frame as a PNG in this folder")
    args = parser.parse_args(argv)

    # 1. read and check all input first, so a bad input never leaves a half-written video
    try:
        out = check_output_path(args.mp4)
        volume = load_volume(args.nrrd)
        planes = read_planes(args.csv)
        projector = Projector(volume)
    except (OSError, ValueError) as e:
        return _fail(e)
    print(f"volume: {volume.shape} {volume.dtype}, planes: {len(planes)}")

    # 2. project every plane
    start = time.perf_counter()
    try:
        images = [projector.project(p) for p in planes]
    except MemoryError:
        return _fail("not enough memory to project the planes (planes too large?)")
    seconds = time.perf_counter() - start
    print(f"projected {len(images)} planes in {seconds:.3f} s ({len(images) / max(seconds, 1e-9):.0f} per second)")

    # 3. one brightness scale for the whole video (FR-11), then write it
    lo, hi = intensity_window(volume)
    frames = [to_uint8(img, lo, hi) for img in images]
    try:
        write_video(frames, out, fps=args.fps)
    except (OSError, RuntimeError, ValueError) as e:
        out.unlink(missing_ok=True)   # never leave a broken, half-written video
        return _fail(f"{out}: could not write the video ({e})")
    print(f"wrote {out}")

    if args.png_dir:
        import imageio.v2 as imageio
        folder = Path(args.png_dir)
        try:
            folder.mkdir(parents=True, exist_ok=True)
            for i, frame in enumerate(frames):
                imageio.imwrite(folder / f"frame_{i:04d}.png", frame)
        except OSError as e:
            return _fail(f"{folder}: could not write the PNG files ({e})")
        print(f"wrote {len(frames)} PNG files to {folder}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
