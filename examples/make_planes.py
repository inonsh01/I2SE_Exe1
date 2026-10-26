"""Generate example plane lists (CSV) for data/MRHead.nrrd (256 x 256 x 130).

MRHead axes: x = face -> back of head, y = top of head -> neck, z = ear -> ear.

Usage: python examples/make_planes.py
"""
import csv
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
X, Y, Z = 256, 256, 130
CENTRE = np.array([(X - 1) / 2, (Y - 1) / 2, (Z - 1) / 2])


def write(name, planes):
    with open(HERE / name, "w", newline="") as f:
        f.write("# one plane per line: a,b,c (9 numbers) or a1,a2,b,c (12 numbers)\n")
        w = csv.writer(f)
        for plane in planes:
            w.writerow([f"{v:.3f}".rstrip("0").rstrip(".") for v in np.ravel(plane)])
    print(f"{name}: {len(planes)} planes")


def rectangle(centre, down, across, half_h, half_w):
    top, bottom = centre - half_h * down, centre + half_h * down
    return [top - half_w * across, top + half_w * across, bottom - half_w * across, bottom + half_w * across]


# 1. horizontal cuts moving from the top of the head down to the neck
write("axial_sweep.csv",
      [[[0, y, 0], [0, y, Z - 1], [X - 1, y, 0], [X - 1, y, Z - 1]] for y in range(10, 250, 2)])

# 2. a plane through the centre, tilting around the ear-to-ear axis (half a turn)
across = np.array([0.0, 0.0, 1.0])
write("rotating.csv",
      [rectangle(CENTRE, np.array([np.cos(t), np.sin(t), 0.0]), across, 128, (Z - 1) / 2)
       for t in np.linspace(0, np.pi, 90, endpoint=False)])

# 3. triangles (3-point form): apex at the face, base across the back of the head
write("triangles.csv",
      [[[0, y, (Z - 1) / 2], [X - 1, y, 0], [X - 1, y, Z - 1]] for y in range(40, 200, 4)])
