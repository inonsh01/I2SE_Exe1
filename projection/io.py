"""File input/output: NRRD volumes, CSV plane lists, MP4 videos.

SRS: FR-1 (load NRRD), FR-9 (read CSV), FR-10 (write MP4), FR-11 (same
brightness scale for every frame).
"""
from __future__ import annotations

import csv
from pathlib import Path

import numpy as np

from .plane import Plane, PlaneError


# --------------------------------------------------------------------- NRRD
def load_volume(path: str | Path) -> np.ndarray:
    """Load a 3D NRRD file as M[x][y][z] (axis order = the file's 'sizes' order)."""
    import nrrd  # pynrrd

    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(f"{path}: file not found")
    try:
        data, _header = nrrd.read(str(path), index_order="F")
    except Exception as e:  # pynrrd raises several error types for bad files
        raise ValueError(f"{path}: not a valid NRRD file ({e})") from None
    if data.ndim != 3:
        raise ValueError(f"{path}: expected a 3D volume, got {data.ndim} dimensions")
    return data


# --------------------------------------------------------------------- CSV
def read_planes(path: str | Path) -> list[Plane]:
    """Read planes from a CSV file: one plane per line, 9 or 12 numbers.

    Blank lines, lines starting with '#', and a header line (first line with
    words instead of numbers) are skipped. Any error names the line number.
    """
    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(f"{path}: file not found")
    planes: list[Plane] = []
    with open(path, newline="") as f:
        for line_no, row in enumerate(csv.reader(f), start=1):
            cells = [c.strip() for c in row if c.strip()]
            if not cells or cells[0].startswith("#"):
                continue
            try:
                numbers = [float(c) for c in cells]
            except ValueError:
                if line_no == 1:
                    continue  # header line
                raise ValueError(f"{path}, line {line_no}: not a number in {cells}") from None
            try:
                planes.append(Plane.from_points(numbers))
            except PlaneError as e:
                raise ValueError(f"{path}, line {line_no}: {e}") from None
    if not planes:
        raise ValueError(f"{path}: no planes found")
    return planes


# --------------------------------------------------------------------- video
def intensity_window(volume: np.ndarray, low_pct: float = 0.5, high_pct: float = 99.5) -> tuple[float, float]:
    """One brightness range for the whole video (FR-11), taken from the volume.

    Percentiles instead of min/max, so a few extreme voxels don't make the
    whole image dark. Every 4th voxel per axis is enough to estimate them.
    """
    sample = volume[::4, ::4, ::4]
    lo, hi = np.percentile(sample, [low_pct, high_pct])
    return float(lo), float(hi)


def to_uint8(image: np.ndarray, lo: float, hi: float) -> np.ndarray:
    """Map values in [lo, hi] to grey levels 0..255 (values outside are clipped)."""
    if hi <= lo:
        hi = lo + 1
    scaled = (image.astype(np.float32) - lo) * (255.0 / (hi - lo))
    return np.clip(scaled, 0, 255).astype(np.uint8)


def write_video(frames: list[np.ndarray], path: str | Path, fps: int = 10) -> None:
    """Write grey uint8 frames (possibly of different sizes) to an MP4 file.

    Every frame is centred on a black canvas as large as the largest frame,
    rounded up to a multiple of 16 (the H.264 video format needs that).
    """
    import imageio.v2 as imageio

    if not frames:
        raise ValueError("no frames to write")
    block = 16
    H = -(-max(f.shape[0] for f in frames) // block) * block
    W = -(-max(f.shape[1] for f in frames) // block) * block
    with imageio.get_writer(str(path), fps=fps, codec="libx264", quality=8,
                            macro_block_size=block, pixelformat="yuv420p") as writer:
        for f in frames:
            canvas = np.zeros((H, W), dtype=np.uint8)
            y0, x0 = (H - f.shape[0]) // 2, (W - f.shape[1]) // 2
            canvas[y0:y0 + f.shape[0], x0:x0 + f.shape[1]] = f
            writer.append_data(np.stack([canvas] * 3, axis=-1))  # grey -> RGB
