"""Unit tests for the projection: TC-J1 ... TC-J12 in docs/TESTING.md."""
import math

import numpy as np
import pytest

from projection import Plane, Projector, project

RNG = np.random.default_rng(0)


def proj(volume, points):
    return project(volume, Plane.from_points(points))


# ----------------------------------------------------------------- TC-J1
def test_tc_j1_axis_aligned_rectangle_equals_slice():
    X, Y, Z = 20, 15, 12
    vol = RNG.integers(0, 60000, (X, Y, Z), dtype=np.uint16)
    y0 = 7
    img = proj(vol, [[0, y0, 0], [0, y0, Z - 1], [X - 1, y0, 0], [X - 1, y0, Z - 1]])
    # row r is at step r+1 along the legs, so the image is the slice from x = 1
    np.testing.assert_array_equal(img, vol[1:, y0, :])


# ----------------------------------------------------------------- TC-J2
def test_tc_j2_worked_example_from_algorithm_doc():
    # 7 x 5 x 1 volume; each cell holds a unique value 10*row + col + 1
    vol = np.zeros((7, 5, 1), dtype=np.uint8)
    for i in range(7):
        for j in range(5):
            vol[i, j, 0] = 10 * j + i + 1
    img = proj(vol, [[3, 0, 0], [0, 4, 0], [6, 4, 0]])

    cell = lambda i, j: 10 * j + i + 1
    expected = np.zeros((5, 7), dtype=np.uint8)
    expected[0, 3] = cell(3, 1)                              # row 0: column 3 only
    expected[1, 2:5] = [cell(2, 2), cell(3, 2), cell(4, 2)]  # row 1
    expected[2, 2:5] = [cell(2, 2), cell(3, 2), cell(4, 2)]  # row 2 (same voxels, see ALGORITHM.md section 5)
    expected[3, 1:6] = [cell(i, 3) for i in range(1, 6)]     # row 3
    expected[4, :] = [cell(i, 4) for i in range(7)]          # row 4: the whole base
    np.testing.assert_array_equal(img, expected)


# ----------------------------------------------------------------- TC-J3, TC-J4
TRI = [[19.5, 0, 20], [0, 39, 20], [39, 39, 20]]


def test_tc_j3_triangle_shape():
    img = proj(np.full((40, 40, 40), 7, np.uint8), TRI)
    filled = img != 0
    assert not filled[0, 0] and not filled[0, -1]       # top corners empty
    assert filled[-1].all()                             # bottom row full
    widths = filled.sum(axis=1)
    assert (np.diff(widths) >= 0).all()                 # rows never get narrower


def test_tc_j4_pixel_filled_iff_centre_inside():
    plane = Plane.from_points(TRI)
    img = project(np.full((40, 40, 40), 7, np.uint8), plane)
    H, W = img.shape
    dab, dbc = plane.leg_length, plane.base_length
    for y in range(H):
        d12 = dbc * (y + 1) / dab                       # row length of an isosceles triangle
        for x in range(W):
            inside = abs(x - dbc / 2) <= d12 / 2 + 1e-9
            assert (img[y, x] != 0) == inside, (x, y)


# ----------------------------------------------------------------- TC-J5..J8 (synthetic volumes)
def test_tc_j5_gradient_constant_x():
    vol = np.broadcast_to(np.arange(64, dtype=np.uint16)[:, None, None] * 1000, (64, 64, 64)).copy()
    img = proj(vol, [[20, 0, 31.5], [20, 63, 0], [20, 63, 63]])
    inside = img[img != 0]
    assert inside.size > 0
    assert (inside == 20000).all()


def _sphere(n=64):
    c = (n - 1) / 2
    x, y, z = np.ogrid[:n, :n, :n]
    return np.where((x - c) ** 2 + (y - c) ** 2 + (z - c) ** 2 <= (n / 3) ** 2, 100000, 0).astype(np.uint32)


def test_tc_j6_sphere_same_circle_at_any_angle():
    vol, centre, r = _sphere(), np.full(3, 31.5), 64 / 3
    rng = np.random.default_rng(1)
    for _ in range(10):
        ed = rng.normal(size=3); ed /= np.linalg.norm(ed)
        ea = np.cross(ed, rng.normal(size=3)); ea /= np.linalg.norm(ea)
        h = 40
        pts = [centre - h * ed - h * ea, centre - h * ed + h * ea, centre + h * ed - h * ea, centre + h * ed + h * ea]
        bright = (proj(vol, pts) == 100000).sum()
        assert bright == pytest.approx(math.pi * r * r, rel=0.05)


def test_tc_j7_cube_square():
    vol = np.zeros((64, 64, 64), np.uint8)
    vol[16:48, 16:48, 16:48] = 200
    img = proj(vol, [[0, 32, 0], [0, 32, 63], [63, 32, 0], [63, 32, 63]])
    rows, cols = np.nonzero(img == 200)
    assert rows.max() - rows.min() + 1 == 32
    assert cols.max() - cols.min() + 1 == 32
    assert (img == 200).sum() == 32 * 32


def test_tc_j8_axes_not_mixed_up():
    vol = np.zeros((10, 40, 25), np.uint8)
    vol[0, 0, 0], vol[-1, 0, 0], vol[0, -1, 0], vol[0, 0, -1] = 50, 100, 150, 250
    # rectangle on the face x = 0; its base (last row) lies on y = 0
    img = proj(vol, [[0, 39, 0], [0, 39, 24], [0, 0, 0], [0, 0, 24]])
    assert img[-1, 0] == 50
    assert img[-1, -1] == 250


# ----------------------------------------------------------------- TC-J9, TC-J10
def test_tc_j9_plane_fully_outside():
    img = proj(np.full((10, 10, 10), 5, np.uint8), [[-50, -50, 5], [-50, -50, 15], [-40, -50, 5], [-40, -50, 15]])
    assert (img == 0).all()


def test_tc_j10_plane_partly_outside():
    img = proj(np.full((10, 10, 10), 3, np.uint8), [[-5, 5, 0], [-5, 5, 9], [14, 5, 0], [14, 5, 9]])
    assert (img == 3).any() and (img == 0).any()


# ----------------------------------------------------------------- TC-J11
@pytest.mark.parametrize("dtype", [np.uint8, np.uint16, np.uint32, np.int16, np.int32])
def test_tc_j11_dtype_preserved(dtype):
    vol = np.full((8, 8, 8), -7 if np.issubdtype(dtype, np.signedinteger) else 7, dtype=dtype)
    img = proj(vol, [[3.5, 0, 4], [0, 7, 4], [7, 7, 4]])
    assert img.dtype == dtype
    assert img[-1, 3] == vol[0, 0, 0]          # negative values survive in signed types


# ----------------------------------------------------------------- TC-J12
@pytest.mark.parametrize("points", [
    [[3, 0, 0], [0, 4, 0], [6, 4, 0]],          # Dab = 5,    Dbc = 6
    [[2.5, 0, 0], [0, 5.2, 0], [5, 5.2, 0]],    # Dab = 5.77, Dbc = 5
    [[0, 0, 0], [0, 0, 9.5], [7.3, 0, 0], [7.3, 0, 9.5]],
])
def test_tc_j12_image_size(points):
    plane = Plane.from_points(points)
    img = project(np.ones((20, 20, 20), np.uint8), plane)
    assert img.shape == (math.ceil(plane.leg_length - 1e-9), math.floor(plane.base_length + 1e-9) + 1)


# ----------------------------------------------------------------- volume checks (FR-2, FR-3)
@pytest.mark.parametrize("bad", [
    np.zeros((4, 4), np.uint8),                 # 2D
    np.zeros((1024, 1, 1), np.uint8),           # too big
    np.zeros((4, 4, 4), np.float32),            # not integers
    np.zeros((4, 4, 4), np.int64),              # 64-bit
])
def test_bad_volume_rejected(bad):
    with pytest.raises(ValueError):
        Projector(bad)
