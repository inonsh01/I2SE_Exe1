# I2SE_Exe1 – Plane Projection of a 3D Volume

Introduction to Software Engineering - Exercise 1

## Problem

We are given a 3D volume M (for example an MRI scan) stored as an NRRD file.
M is a 3D matrix of size sx × sy × sz (1 ≤ sx, sy, sz < 1024), where every
entry M[x][y][z] is an unsigned integer value (8, 16 or 32 bits).

We are also given a plane p, defined by:
- 3 points (a, b, c) forming an isosceles triangle: |dist(a,b) − dist(a,c)| < EPS, or
- 4 points (a1, a2, b, c) forming an isosceles trapezoid.

The goal is to compute the 2D image (matrix) of the cut of M along p, at any
angle – similar to the X/Y/Z slice views in 3D Slicer, but for any plane.

Given a list of planes (CSV), the program renders one image per plane and
saves them as a video (MP4).

## Scope

### In scope
- Reading 3D volumes in NRRD format (8/16/32-bit integer voxels).
- Defining a plane by 3 points (triangle) or 4 points (trapezoid), and
  validating it.
- Projecting a plane to a 2D image using the course algorithm.
- Points outside the volume are drawn as 0 (black).
- A demo: `python Ex0.py file.nrrd file.csv file.mp4`.
- Performance: at least 30 FPS on a 500³ volume (target: 100+ FPS).
- Tests and documentation (README, SRS).

### Out of scope
- A graphical user interface (GUI).
- File formats other than NRRD (e.g. DICOM).
- Physical/world coordinates: plane points are given in voxel indices.

## Documents
- [Software Requirements Specification (SRS)](docs/SRS.md)
- [Algorithm](docs/ALGORITHM.md)
- [Data set](data/README.md)
- [Testing strategy](docs/TESTING.md)
