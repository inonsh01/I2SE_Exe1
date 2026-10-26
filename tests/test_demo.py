"""End-to-end tests of the demo Ex0.py: TC-D1 ... TC-D7 in docs/TESTING.md."""
import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
CUBE = ROOT / "data" / "synthetic_cube.nrrd"           # 64^3, bright cube 16..47 (value 200)

# three planes through the cube: horizontal rectangle, vertical rectangle, triangle
THREE_PLANES = (
    "# test planes\n"
    "0,32,0, 0,32,63, 63,32,0, 63,32,63\n"
    "32,0,0, 32,0,63, 32,63,0, 32,63,63\n"
    "0,32,31.5, 63,32,0, 63,32,63\n"
)


def run_demo(*args):
    """Run Ex0.py exactly like a user does, from the command line."""
    return subprocess.run([sys.executable, str(ROOT / "Ex0.py"), *map(str, args)],
                          capture_output=True, text=True, cwd=ROOT)


@pytest.fixture
def planes_csv(tmp_path):
    f = tmp_path / "planes.csv"
    f.write_text(THREE_PLANES)
    return f


def test_tc_d1_video_has_one_frame_per_plane(tmp_path, planes_csv):
    import imageio.v2 as imageio
    out = tmp_path / "out.mp4"
    r = run_demo(CUBE, planes_csv, out)
    assert r.returncode == 0, r.stderr
    assert out.is_file()
    assert imageio.get_reader(str(out)).count_frames() == 3


def test_tc_d2_frames_in_csv_order(tmp_path, planes_csv):
    import imageio.v2 as imageio
    from projection import Plane, Projector
    from projection.io import intensity_window, load_volume, to_uint8

    r = run_demo(CUBE, planes_csv, tmp_path / "out.mp4", "--png-dir", tmp_path / "png")
    assert r.returncode == 0, r.stderr
    volume = load_volume(CUBE)
    lo, hi = intensity_window(volume)
    lines = [l for l in THREE_PLANES.splitlines() if l and not l.startswith("#")]
    for i, line in enumerate(lines):
        expected = to_uint8(Projector(volume).project(Plane.from_points([float(v) for v in line.split(",")])), lo, hi)
        frame = imageio.imread(tmp_path / "png" / f"frame_{i:04d}.png")
        np.testing.assert_array_equal(frame, expected)


def test_tc_d3_cube_visible(tmp_path, planes_csv):
    import imageio.v2 as imageio
    r = run_demo(CUBE, planes_csv, tmp_path / "out.mp4", "--png-dir", tmp_path / "png")
    assert r.returncode == 0, r.stderr
    frame = imageio.imread(tmp_path / "png" / "frame_0000.png")
    assert frame.max() == 255 and frame.min() == 0           # bright cube on black
    assert (frame == 255).sum() == 32 * 32


def test_tc_d4_triangles_and_rectangles_mixed(tmp_path, planes_csv):
    r = run_demo(CUBE, planes_csv, tmp_path / "out.mp4")     # lines 1-2: 12 numbers, line 3: 9
    assert r.returncode == 0, r.stderr
    assert "planes: 3" in r.stdout


def test_tc_d5_missing_nrrd(tmp_path, planes_csv):
    out = tmp_path / "out.mp4"
    r = run_demo(tmp_path / "missing.nrrd", planes_csv, out)
    assert r.returncode != 0
    assert "not found" in r.stderr
    assert not out.exists()


def test_tc_d6_invalid_plane_in_csv(tmp_path):
    bad = tmp_path / "bad.csv"
    bad.write_text("0,32,31.5, 63,32,0, 63,32,63\n0,0,0, 0,10,0, 3,3,0\n")
    out = tmp_path / "out.mp4"
    r = run_demo(CUBE, bad, out)
    assert r.returncode != 0
    assert "line 2" in r.stderr and "legs differ" in r.stderr
    assert not out.exists()


def test_tc_d7_wrong_arguments(tmp_path):
    r = run_demo(CUBE)
    assert r.returncode != 0
    assert "usage" in r.stderr.lower()
