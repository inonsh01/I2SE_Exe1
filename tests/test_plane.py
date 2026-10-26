"""Unit tests for plane validation: TC-P1 ... TC-P14 in docs/TESTING.md."""
import dataclasses

import numpy as np
import pytest

from projection import Plane, PlaneError

TRIANGLE = [[3, 0, 0], [0, 4, 0], [6, 4, 0]]            # legs 5, base 6
RECTANGLE = [[0, 0, 0], [0, 0, 9], [9, 0, 0], [9, 0, 9]]  # a1, a2, b, c


def test_tc_p1_isosceles_triangle_accepted():
    p = Plane.from_points(TRIANGLE)
    assert p.is_triangle
    assert p.leg_length == pytest.approx(5)
    assert p.base_length == pytest.approx(6)


def test_tc_p1_flat_list_of_9_numbers():
    p = Plane.from_points([3, 0, 0, 0, 4, 0, 6, 4, 0])
    assert p.leg_length == pytest.approx(5)


def test_tc_p2_legs_within_eps_accepted():
    Plane.from_points([[0, 0, 0], [0, 10, 0], [0, 0, 10.0005]])


def test_tc_p3_legs_beyond_eps_rejected():
    with pytest.raises(PlaneError, match="legs differ"):
        Plane.from_points([[0, 0, 0], [0, 10, 0], [0, 0, 10.01]])


def test_tc_p4_collinear_rejected():
    # isosceles (both legs 5) but all on one line
    with pytest.raises(PlaneError, match="collinear"):
        Plane.from_points([[0, 0, 0], [0, 5, 0], [0, -5, 0]])


@pytest.mark.parametrize("pts", [
    [[0, 0, 0], [3, 4, 0], [3, 4, 0]],   # b == c
    [[0, 0, 0], [0, 0, 0], [0, 0, 0]],   # all the same
])
def test_tc_p5_equal_points_rejected(pts):
    with pytest.raises(PlaneError):
        Plane.from_points(pts)


def test_tc_p6_rectangle_accepted():
    p = Plane.from_points(RECTANGLE)
    assert not p.is_triangle
    assert p.leg_length == pytest.approx(9)


def test_tc_p6_flat_list_of_12_numbers():
    Plane.from_points(sum(RECTANGLE, []))


def test_tc_p7_top_wider_than_base_rejected():
    # legs both sqrt(125), but top (20) is wider than base (10)
    with pytest.raises(PlaneError, match="<= dist"):
        Plane.from_points([[-5, 0, 0], [15, 0, 0], [0, 10, 0], [10, 10, 0]])


def test_tc_p8_not_coplanar_rejected():
    # legs both 10, but a2 is off the plane of a1, b, c
    with pytest.raises(PlaneError, match="same plane"):
        Plane.from_points([[0, 0, 0], [10, 0, 0], [0, 10, 0], [10, 6, 8]])


@pytest.mark.parametrize("pts", [
    [1, 2, 3, 4, 5, 6, 7],                   # 7 numbers
    [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],         # 10 numbers
    [[1, 2], [3, 4], [5, 6]],                # 2D points
    [["a", 0, 0], [0, 4, 0], [6, 4, 0]],     # not numbers
    [[float("nan"), 0, 0], [0, 4, 0], [6, 4, 0]],
])
def test_tc_p9_wrong_input_rejected(pts):
    with pytest.raises(PlaneError):
        Plane.from_points(pts)


# ----------------------------------------------------------------- TC-P10..P13
def test_tc_p10_isosceles_trapezoid_accepted():
    # top 4 wide, base 10 wide, symmetric around x = 5; legs both sqrt(9 + 64)
    p = Plane.from_points([[3, 0, 0], [7, 0, 0], [0, 8, 0], [10, 8, 0]])
    assert not p.is_triangle


@pytest.mark.parametrize("pts, rule", [
    ([[7, 0, 0], [3, 0, 0], [0, 8, 0], [10, 8, 0]], "legs cross"),        # a1 and a2 swapped
    ([[0, 0, 0], [0, 0, 4], [10, 0, -2], [2, 0, 14]], "parallel"),         # equal legs, sides not parallel
    ([[0, 0, 0], [4, 0, 0], [1, 5, 0], [5, 5, 0]], "not symmetric"),       # parallelogram
])
def test_tc_p11_not_an_isosceles_trapezoid_rejected(pts, rule):
    with pytest.raises(PlaneError, match=rule):
        Plane.from_points(pts)


@pytest.mark.parametrize("pts", [
    [[0, 0, 0], [1e5, 0, 0], [0, 1e5, 0]],                                  # legs too long
    [[0, 0, 0], [0, 0, 5000], [3000, 0, 0], [3000, 0, 5000]],              # base too long
])
def test_tc_p12_plane_too_large_rejected(pts):
    with pytest.raises(PlaneError, match="too large"):
        Plane.from_points(pts)


def test_tc_p13_coordinates_too_far_rejected():
    with pytest.raises(PlaneError, match="between"):
        Plane.from_points([[1e9, 0, 0], [1e9 - 3, 4, 0], [1e9 + 3, 4, 0]])


# ----------------------------------------------------------------- TC-P14 (DESIGN.md §4.1)
def test_tc_p14_plane_cannot_be_changed():
    p = Plane.from_points(TRIANGLE)
    with pytest.raises(dataclasses.FrozenInstanceError):
        p.b = np.zeros(3)
    with pytest.raises(ValueError, match="read-only"):
        p.b[0] = 100
    assert p.leg_length == pytest.approx(5)


def test_tc_p14_caller_arrays_are_copied():
    pts = np.array(TRIANGLE, dtype=float)
    p = Plane.from_points(pts)
    pts[1, 0] = 100                       # change the caller's array afterwards
    assert p.leg_length == pytest.approx(5)


def test_tc_p14_constructor_validates_too():
    z = np.zeros(3)
    with pytest.raises(PlaneError):
        Plane(z, z, z, z)
    with pytest.raises(PlaneError, match="legs differ"):
        Plane([0, 0, 0], [0, 0, 0], [0, 10, 0], [0, 0, 10.01])
    assert Plane([3, 0, 0], [3, 0, 0], [0, 4, 0], [6, 4, 0]) == Plane.from_points(TRIANGLE)


def test_tc_p14_equality_and_hash():
    p, q = Plane.from_points(TRIANGLE), Plane.from_points(sum(TRIANGLE, []))
    r = Plane.from_points(RECTANGLE)
    assert p == q and hash(p) == hash(q)
    assert p != r
    assert len({p, q, r}) == 2
