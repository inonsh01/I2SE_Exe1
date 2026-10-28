# Software Requirements Specification (SRS)
## Plane Projection of a 3D Volume – I2SE Ex1

Version 0.3

| Version | Change |
| --- | --- |
| 0.1 | First version. |
| 0.3 | FR-9: optional leading point count (3 or 4), the format some classmates' CSV files use. |
| 0.2 | FR-5: a 4-point plane must be a real isosceles trapezoid. FR-9: other separators, header rule. New FR-12 (plane size limit) and FR-13 (output path). NFR-2 states the first-row offset. |

---

## 1. Introduction

### 1.1 Purpose
This document defines **what** the software must do: its inputs, outputs,
behaviour and quality requirements. It does not describe **how** it is
implemented; the algorithm is described separately.

### 1.2 Product overview
A command-line program that loads a 3D volume (e.g. an MRI scan), cuts it
along one or more user-given planes, and saves the resulting 2D images as a
video, one frame per plane.

### 1.3 Definitions

| Term | Meaning |
| --- | --- |
| Volume (M) | A 3D matrix of size sx × sy × sz, where 1 ≤ sx, sy, sz < 1024. |
| Voxel | One cell of the volume, M[x][y][z]. Holds an integer of 8, 16 or 32 bits. |
| Plane (p) | A cut through the volume, given by 3 points (triangle) or 4 points (trapezoid). |
| Projection | The 2D image of the volume's values on the plane. |
| EPS | Tolerance for comparing lengths: 0.001. |
| NRRD | A file format for 3D raster data, used by 3D Slicer. |
| FPS | Frames (projections) computed per second. |

### 1.4 References
- Course assignment: "Ex1: Algorithm: Implementing a plane projection of 3D volume".
- NRRD format: http://teem.sourceforge.net/nrrd/format.html
- 3D Slicer: https://www.slicer.org

---

## 2. Overall description

### 2.1 Users
- **Grader / student:** runs the demo from the command line.
- **Developer:** calls the projection code from their own program.

### 2.2 Operating environment
- macOS, Linux or Windows with Python 3.10 or newer.
- Runs on a regular laptop; no GPU required.

### 2.3 Constraints
- Language: Python (allowed by the assignment: Java / Python / C / C++).
- Input volume format: NRRD only.
- Output format: MP4 video.

### 2.4 Assumptions
- Plane points are given in voxel coordinates (cell indices), not in
  millimetres.
- Every voxel is treated as a 1 × 1 × 1 cube (voxel spacing is ignored).

---

## 3. External interfaces

### 3.1 Command line
```
python Ex0.py <file.nrrd> <file.csv> <file.mp4>
```

| Argument | Description |
| --- | --- |
| `file.nrrd` | The 3D volume to cut. |
| `file.csv` | A list of planes, one per line. |
| `file.mp4` | The output video to create. |

### 3.2 Plane file (CSV)
- One plane per line.
- Numbers are separated by commas, semicolons, spaces or tabs.
- 9 numbers = 3 points: `ax,ay,az, bx,by,bz, cx,cy,cz`
- 12 numbers = 4 points: `a1x,a1y,a1z, a2x,a2y,a2z, bx,by,bz, cx,cy,cz`
- A line may also start with the number of points: `3,ax,…,cz` (10 numbers) or
  `4,a1x,…,cz` (13 numbers). The count must match the coordinates. Empty cells at
  the end of a line (`,,,`) are ignored. The point order is the same: a1, a2, b, c.
- Empty lines and lines starting with `#` are ignored.
- The first other line may be a header (only words, no numbers, e.g. `ax,ay,az,...`).
  Any other line with text in it is an error, so a typo is never skipped silently.
- Every coordinate must be between −10⁶ and 10⁶.

Example:
```
# triangle
0,100,64.5, 255,100,0, 255,100,129
# rectangle
0,50,0, 0,50,129, 255,50,0, 255,50,129
```

### 3.3 Output video
- One frame per plane, in the same order as the CSV.
- Grayscale.

---

## 4. Functional requirements

| ID | Requirement |
| --- | --- |
| **FR-1** | The system shall load a 3D volume from an NRRD file. |
| **FR-2** | The system shall support voxel values of 8, 16 and 32 bits, unsigned (as in the assignment) and signed (as in real scans, see [data set](../data/README.md)). |
| **FR-3** | The system shall reject a volume that is not 3D, or whose size is outside 1 ≤ s < 1024, with a clear error message. |
| **FR-4** | The system shall accept a plane defined by 3 points (a, b, c) where \|dist(a,b) − dist(a,c)\| < EPS. |
| **FR-5** | The system shall accept a plane defined by 4 points (a1, a2, b, c) where \|dist(a1,b) − dist(a2,c)\| < EPS, dist(a1,a2) ≤ dist(b,c), and all 4 points lie on the same plane (the rules in the assignment). In addition, the shape must really be an isosceles trapezoid: a1–a2 parallel to b–c and pointing the same way (the legs do not cross), and symmetric (not a parallelogram). |
| **FR-6** | The system shall reject an invalid plane (e.g. not isosceles, points on one line) with a message that says which rule failed and on which CSV line. |
| **FR-7** | The system shall compute the 2D projection of the volume on a given plane, using the course algorithm. |
| **FR-8** | Points of the plane that fall outside the volume shall get the value 0. |
| **FR-9** | The system shall read a list of planes from a CSV file (format in §3.2). |
| **FR-10** | The system shall save the projections of all planes as an MP4 video, one frame per plane, in CSV order. |
| **FR-11** | The brightness scale shall be the same for all frames of one video, so the video does not flicker. |
| **FR-12** | The system shall reject a plane whose legs or base are longer than 4096 voxels (more than twice the largest diagonal of any allowed volume), with a clear message, instead of running out of memory. |
| **FR-13** | The system shall check, before doing any work, that the output file can be created (its folder exists, the name ends with `.mp4`), and shall report a failure while writing the video as an error, without leaving a broken file. |

---

## 5. Non-functional requirements

| ID | Category | Requirement |
| --- | --- | --- |
| **NFR-1** | Performance | For a 500³ volume, the system shall compute at least **30 projections per second** (required), with a target of **100+ per second**. |
| **NFR-2** | Correctness | A rectangle aligned with the volume's axes shall give exactly the same values as the matching slice of the volume, starting one row below the top edge a1–a2 (the course algorithm steps before it samples, see ALGORITHM.md §3 #4). |
| **NFR-3** | Robustness | The system shall not crash on invalid input (missing file, bad CSV, plane outside the volume, huge plane, bad output path). It shall print a one-line error (never a Python traceback) and exit with a non-zero code. |
| **NFR-4** | Maintainability | The code shall be split into separate modules: file input/output, plane definition, and projection. |
| **NFR-5** | Testability | Every functional requirement shall be covered by at least one automated test. |
| **NFR-6** | Portability | The system shall run on macOS, Linux and Windows with only free, open-source libraries. |
