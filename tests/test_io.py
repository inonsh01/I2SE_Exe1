"""Unit tests for file input/output: TC-IO1 ... TC-IO12 in docs/TESTING.md."""
from pathlib import Path

import numpy as np
import pytest

from projection.io import check_output_path, intensity_window, load_volume, read_planes, to_uint8, write_video

DATA = Path(__file__).resolve().parents[1] / "data"


# ----------------------------------------------------------------- TC-IO1
@pytest.mark.parametrize("name, shape, dtype", [
    ("synthetic_cube.nrrd", (64, 64, 64), np.uint8),
    ("synthetic_gradient.nrrd", (64, 64, 64), np.uint16),
    ("synthetic_sphere.nrrd", (64, 64, 64), np.uint32),
    ("synthetic_odd_shape.nrrd", (10, 40, 25), np.uint8),
])
def test_tc_io1_load_synthetic(name, shape, dtype):
    vol = load_volume(DATA / name)
    assert vol.shape == shape and vol.dtype == dtype


def test_tc_io1_axis_order():
    vol = load_volume(DATA / "synthetic_odd_shape.nrrd")
    assert (vol[0, 0, 0], vol[-1, 0, 0], vol[0, -1, 0], vol[0, 0, -1]) == (50, 100, 150, 250)


# ----------------------------------------------------------------- TC-IO2
def test_tc_io2_2d_nrrd_rejected(tmp_path):
    import nrrd
    nrrd.write(str(tmp_path / "flat.nrrd"), np.zeros((5, 5), np.uint8))
    with pytest.raises(ValueError, match="3D"):
        load_volume(tmp_path / "flat.nrrd")


def test_missing_file(tmp_path):
    with pytest.raises(FileNotFoundError, match="not found"):
        load_volume(tmp_path / "nope.nrrd")
    with pytest.raises(FileNotFoundError, match="not found"):
        read_planes(tmp_path / "nope.csv")


def test_not_an_nrrd_file(tmp_path):
    (tmp_path / "bad.nrrd").write_text("hello")
    with pytest.raises(ValueError, match="not a valid NRRD"):
        load_volume(tmp_path / "bad.nrrd")


# ----------------------------------------------------------------- TC-IO3..6
def test_tc_io3_csv_formats(tmp_path):
    f = tmp_path / "p.csv"
    f.write_text("ax,ay,az,bx,by,bz,cx,cy,cz\n"
                 "# a triangle\n"
                 "3,0,0, 0,4,0, 6,4,0\n"
                 "\n"
                 "0,0,0, 0,0,9, 9,0,0, 9,0,9\n")
    planes = read_planes(f)
    assert len(planes) == 2
    assert planes[0].is_triangle and not planes[1].is_triangle


def test_tc_io4_non_number(tmp_path):
    f = tmp_path / "p.csv"
    f.write_text("3,0,0,0,4,0,6,4,0\n3,0,x,0,4,0,6,4,0\n")
    with pytest.raises(ValueError, match="line 2"):
        read_planes(f)


def test_tc_io5_invalid_plane_names_line_and_rule(tmp_path):
    f = tmp_path / "p.csv"
    f.write_text("3,0,0,0,4,0,6,4,0\n3,0,0,0,4,0,6,4,0\n0,0,0,0,10,0,3,3,0\n")
    with pytest.raises(ValueError, match=r"line 3: legs differ"):
        read_planes(f)


def test_tc_io6_empty_csv(tmp_path):
    f = tmp_path / "p.csv"
    f.write_text("# nothing here\n\n")
    with pytest.raises(ValueError, match="no planes"):
        read_planes(f)


# ----------------------------------------------------------------- TC-IO7
def test_tc_io7_video_frame_count_and_sizes(tmp_path):
    import imageio.v2 as imageio
    frames = [np.full((30, 40), 255, np.uint8), np.zeros((50, 20), np.uint8), np.full((10, 10), 128, np.uint8)]
    out = tmp_path / "v.mp4"
    write_video(frames, out)
    reader = imageio.get_reader(str(out))
    assert reader.count_frames() == 3
    first = reader.get_data(0)
    assert first.shape[0] % 16 == 0 and first.shape[1] % 16 == 0
    assert first.shape[0] >= 50 and first.shape[1] >= 40


# ----------------------------------------------------------------- brightness (FR-11)
def test_to_uint8_and_window():
    vol = np.arange(1000, dtype=np.int16).reshape(10, 10, 10) - 500   # -500 .. 499, signed
    lo, hi = intensity_window(vol, 0, 100)
    img = to_uint8(vol[:, :, 0], lo, hi)
    assert img.dtype == np.uint8
    assert img.min() == 0 and img.max() > 200
    assert to_uint8(np.array([[lo - 100, hi + 100]]), lo, hi).tolist() == [[0, 255]]   # clipped


# ----------------------------------------------------------------- TC-IO8..IO11
def test_tc_io8_typo_in_first_line_is_an_error_not_a_header(tmp_path):
    f = tmp_path / "p.csv"
    f.write_text("3,0,0, 0,4,0, 6,4,0x\n3,0,0, 0,4,0, 6,4,0\n")
    with pytest.raises(ValueError, match=r"line 1: not a number: 0x"):
        read_planes(f)


def test_tc_io9_header_after_comment_lines(tmp_path):
    f = tmp_path / "p.csv"
    f.write_text("# my planes\n\nax,ay,az,bx,by,bz,cx,cy,cz\n3,0,0, 0,4,0, 6,4,0\n")
    assert len(read_planes(f)) == 1


def test_tc_io9_only_one_header_allowed(tmp_path):
    f = tmp_path / "p.csv"
    f.write_text("ax,ay,az,bx,by,bz,cx,cy,cz\nax,ay,az,bx,by,bz,cx,cy,cz\n3,0,0, 0,4,0, 6,4,0\n")
    with pytest.raises(ValueError, match="line 2"):
        read_planes(f)


@pytest.mark.parametrize("line", [
    "3 0 0 0 4 0 6 4 0",            # spaces
    "3;0;0;0;4;0;6;4;0",            # semicolons (European Excel)
    "3\t0\t0\t0\t4\t0\t6\t4\t0",    # tabs
    "\ufeff3,0,0,0,4,0,6,4,0",      # byte-order mark from Excel
])
def test_tc_io10_other_separators(tmp_path, line):
    f = tmp_path / "p.csv"
    f.write_text(line + "\n", encoding="utf-8")
    assert len(read_planes(f)) == 1


def test_tc_io11_output_path_checked(tmp_path):
    assert check_output_path(tmp_path / "out.mp4") == tmp_path / "out.mp4"
    with pytest.raises(FileNotFoundError, match="does not exist"):
        check_output_path(tmp_path / "no_such_folder" / "out.mp4")
    with pytest.raises(ValueError, match=".mp4"):
        check_output_path(tmp_path / "out.avi")
    (tmp_path / "x.mp4").mkdir()
    with pytest.raises(IsADirectoryError):
        check_output_path(tmp_path / "x.mp4")


# ----------------------------------------------------------------- TC-IO12
def test_tc_io12_leading_point_count(tmp_path):
    f = tmp_path / "p.csv"
    f.write_text("Number of Points (3 or 4),x1,y1,z1,x2,y2,z2,x3,y3,z3,x4,y4,z4\n"
                 "3,3,0,0,0,4,0,6,4,0,,,\n"
                 "4,0,0,0,0,0,9,9,0,0,9,0,9\n"
                 "3,0,0,0, 0,0,9, 9,0,0, 9,0,9\n")          # 13 numbers led by 3: wrong
    with pytest.raises(ValueError, match=r"line 4: the line says 3 points but has 12"):
        read_planes(f)
    f.write_text("Number of Points (3 or 4),x1,y1,z1,x2,y2,z2,x3,y3,z3,x4,y4,z4\n"
                 "3,3,0,0,0,4,0,6,4,0,,,\n"
                 "4,0,0,0,0,0,9,9,0,0,9,0,9\n")
    with_count = read_planes(f)
    f.write_text("3,0,0,0,4,0,6,4,0\n0,0,0,0,0,9,9,0,0,9,0,9\n")
    assert with_count == read_planes(f)                        # same planes as without the count


def test_tc_io12_bad_count_rejected(tmp_path):
    f = tmp_path / "p.csv"
    f.write_text("5,3,0,0,0,4,0,6,4,0\n")
    with pytest.raises(ValueError, match=r"line 1: .*number of points \(3 or 4\), but it is 5"):
        read_planes(f)
