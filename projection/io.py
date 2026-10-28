"""File input/output: NRRD volumes, CSV plane lists, MP4 videos.

SRS: FR-1 (load NRRD), FR-9 (read CSV), FR-10 (write MP4), FR-11 (same
brightness scale for every frame).
"""
from __future__ import annotations

import re
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
_SEPARATORS = re.compile(r"[,;\s]+")   # comma, semicolon or whitespace


def _to_number(cell: str) -> float | None:
    try:
        return float(cell)
    except ValueError:
        return None


def _drop_point_count(numbers: list[float]) -> list[float]:
    """10 or 13 numbers = a leading point count (3 or 4) + the coordinates."""
    if len(numbers) not in (10, 13):
        return numbers                        # 9 or 12: no count; anything else: Plane reports it
    count, coords = numbers[0], numbers[1:]
    if count not in (3, 4):
        raise PlaneError(f"got {len(numbers)} numbers, so the first should be the number "
                         f"of points (3 or 4), but it is {count:g}")
    if len(coords) != 3 * count:
        raise PlaneError(f"the line says {count:g} points but has {len(coords)} coordinates "
                         f"(expected {3 * int(count)})")
    return coords


def read_planes(path: str | Path) -> list[Plane]:
    """Read planes from a CSV file: one plane per line, 9 or 12 numbers.

    A line may also start with the number of points (3 or 4), as in
    "3,ax,ay,az,bx,by,bz,cx,cy,cz" (10 numbers) or "4,..." (13 numbers);
    the count must match the coordinates that follow. Empty cells at the
    end of a line (",,,") are ignored. Numbers may be separated by commas, semicolons or spaces. Blank lines and
    lines starting with '#' are skipped. The first non-comment line is
    skipped as a header only if it contains no numbers at all (for example
    "ax,ay,az,..."). A line that mixes numbers and text is always an error,
    so a typo in the first plane is never dropped silently. Any error names
    the line number.
    """
    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(f"{path}: file not found")
    planes: list[Plane] = []
    header_allowed = True
    with open(path, encoding="utf-8-sig") as f:   # utf-8-sig: ignore a BOM from Excel
        for line_no, line in enumerate(f, start=1):
            text = line.strip()
            if not text or text.startswith("#"):
                continue
            cells = [c for c in _SEPARATORS.split(text) if c]
            numbers = [_to_number(c) for c in cells]
            if None in numbers:
                if header_allowed and all(n is None for n in numbers):
                    header_allowed = False
                    continue  # header line
                bad = [c for c, n in zip(cells, numbers) if n is None]
                raise ValueError(f"{path}, line {line_no}: not a number: {', '.join(bad)}")
            header_allowed = False
            try:
                planes.append(Plane.from_points(_drop_point_count(numbers)))
            except PlaneError as e:
                raise ValueError(f"{path}, line {line_no}: {e}") from None
    if not planes:
        raise ValueError(f"{path}: no planes found")
    return planes


def check_output_path(path: str | Path) -> Path:
    """Fail early (before any work) if the output file cannot be created."""
    path = Path(path)
    folder = path.parent if str(path.parent) else Path(".")
    if not folder.is_dir():
        raise FileNotFoundError(f"{path}: output folder {folder} does not exist")
    if path.is_dir():
        raise IsADirectoryError(f"{path}: is a folder, not a file name")
    if path.suffix.lower() != ".mp4":
        raise ValueError(f"{path}: the output file must end with .mp4")
    return path


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
