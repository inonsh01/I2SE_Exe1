# Testing Strategy

This document defines how we check that the program meets the
[SRS](SRS.md). Every requirement (FR / NFR) is covered by at least one test
case (TC), see the traceability table in [section 7](#7-traceability-requirement--tests).

---

## 1. Goals

1. **Correctness:** the image for a plane is exactly what the
   [algorithm](ALGORITHM.md) defines.
2. **Robustness:** bad input gives a clear error, never a crash.
3. **Performance:** at least 30 FPS on a 500³ volume (NFR-1).
4. **The demo works end to end:** `python Ex0.py file.nrrd file.csv file.mp4`
   produces the right video.

## 2. Tools

| Tool | Use |
| --- | --- |
| `pytest` | Runs all automated tests: `python -m pytest` |
| Synthetic volumes ([data set](../data/README.md)) | Inputs where the correct answer is known in advance |
| Real scans (MRHead, CTChest, …) | Realistic sizes and types; visual check |
| `benchmarks/bench.py` | Measures FPS |

## 3. Test levels

| Level | What is tested | How |
| --- | --- | --- |
| **Unit** | One module at a time: plane validation, projection, CSV parsing, video writing | Small inputs built inside the test |
| **Integration** | The modules together: NRRD file → projection → image | Synthetic NRRD files from `data/` |
| **End-to-end (demo)** | `Ex0.py` as a user runs it, from the command line | Real files in, MP4 out; exit code and output checked |
| **Performance** | Speed of the projection | Benchmark on a random 500³ volume |
| **Visual (manual)** | That the images "look right" | We watch the demo videos of real scans |

---

## 4. Unit tests

### 4.1 Plane validation (`plane.py`)

| ID | Input | Expected |
| --- | --- | --- |
| TC-P1 | Isosceles triangle `a=(3,0,0) b=(0,4,0) c=(6,4,0)` | Accepted |
| TC-P2 | Legs differ by less than EPS (0.0005) | Accepted |
| TC-P3 | Legs differ by more than EPS (0.01) | Rejected: "legs differ" |
| TC-P4 | `a, b, c` on one line | Rejected: "collinear" |
| TC-P5 | Two points equal (`b = c`) | Rejected |
| TC-P6 | Valid rectangle (4 points) | Accepted |
| TC-P7 | Trapezoid with top wider than base, `dist(a1,a2) > dist(b,c)` | Rejected |
| TC-P8 | 4 points not on one plane | Rejected: "not on the same plane" |
| TC-P9 | Wrong count of numbers (e.g. 7 or 10) | Rejected |
| TC-P10 | Isosceles trapezoid that is not a rectangle | Accepted |
| TC-P11 | Equal legs but not an isosceles trapezoid: legs cross, sides not parallel, parallelogram | Rejected, message names the rule |
| TC-P12 | Legs or base longer than 4096 voxels | Rejected: "too large" |
| TC-P13 | A coordinate beyond ±10⁶ | Rejected |
| TC-P14 | A plane after it was created ([DESIGN.md, section 4.1](DESIGN.md#41-plane-is-an-immutable-value-object-with-a-factory-method)) | Cannot be changed (frozen, read-only points, caller's array copied); `Plane(...)` validates like `from_points`; equal points → `==` and same `hash` |

### 4.2 Projection (`projector.py`)

Each case uses a synthetic volume whose correct result we can compute by hand.

| ID | Volume | Plane | Expected |
| --- | --- | --- | --- |
| TC-J1 | Random 20×15×12 | Rectangle at `y = 7`, along x and z | Image equals the slice `M[1:, 7, :]` exactly (row `r` is at step `r+1`) |
| TC-J2 | Hand-made 7×5×1 | The triangle from [ALGORITHM.md, section 5](ALGORITHM.md#5-worked-example) | Exactly the 5×7 image in the worked example |
| TC-J3 | Constant volume | Any triangle | Filled pixels form a triangle: row widths never shrink, top corners are 0, bottom row is full |
| TC-J4 | Constant volume | Every pixel | A pixel is non-zero **iff** `\|x − Dbc/2\| ≤ d12/2` |
| TC-J5 | `synthetic_gradient` (value = 1000·x) | Plane at constant `x = 20` | Every pixel inside the triangle is 20000 |
| TC-J6 | `synthetic_sphere` | 10 random angles through the centre | Bright pixel count ≈ π·r² (within 5%) for every angle |
| TC-J7 | `synthetic_cube` | Axis-aligned cut through the centre | A 32×32 bright square |
| TC-J8 | `synthetic_odd_shape` | Rectangle on the face `x = 0`, base on `y = 0` | Bottom-left pixel = 50, bottom-right = 250 (axes not mixed up) |
| TC-J9 | Any | Plane completely outside the volume | All pixels 0, no error |
| TC-J10 | Any | Plane partly outside | Outside part 0, inside part correct |
| TC-J11 | uint8 / uint16 / uint32 / int16 / int32 | Any | Output keeps the input type |
| TC-J12 | Any | Image size | `H = ceil(Dab)`, `W = floor(Dbc) + 1` |

### 4.3 Input / output (`io.py`)

| ID | Input | Expected |
| --- | --- | --- |
| TC-IO1 | NRRD file of each synthetic volume | Loaded with the right shape and type |
| TC-IO2 | 2D NRRD file | Rejected: "expected a 3D volume" |
| TC-IO3 | CSV with comments, blank lines, 9- and 12-number rows | Correct list of planes |
| TC-IO4 | CSV with a non-number | Rejected, the message names the line |
| TC-IO5 | CSV with an invalid plane on line 3 | Rejected, the message says line 3 and the rule |
| TC-IO6 | Empty CSV | Rejected: "no planes found" |
| TC-IO7 | Video from frames of different sizes | MP4 is written; frame count equals the number of planes |
| TC-IO8 | Typo in the **first** line (`6,4,0x`) | Rejected with "line 1", not skipped as a header |
| TC-IO9 | Header after comment lines; two header lines | First is skipped; the second is an error |
| TC-IO10 | Spaces, semicolons, tabs, Excel byte-order mark | Read correctly |
| TC-IO11 | Output path: missing folder, not `.mp4`, a folder | Rejected before any work |
| TC-IO12 | Lines led by the point count (`3,…` / `4,…`), header `Number of Points (3 or 4),x1,…`, empty cells at the end | Same planes as without the count; a wrong count (`4` with 9 coordinates, `5,…`) is rejected with the line number |

---

## 5. End-to-end tests: the demo (`Ex0.py`)

The demo is the part graders run, so it gets its own tests. Each one runs
`Ex0.py` exactly as a user would and checks the result.

| ID | Command / input | Expected |
| --- | --- | --- |
| TC-D1 | `Ex0.py cube.nrrd planes.csv out.mp4` (3 planes) | Exit code 0; `out.mp4` exists; it has **3 frames** |
| TC-D2 | Same, frames in CSV order | Frame *i* matches the projection of CSV line *i* |
| TC-D3 | Cut through the bright cube | The frame shows a bright area on black |
| TC-D4 | Mix of triangles (9 numbers) and rectangles (12) in one CSV | Exit code 0, one frame each |
| TC-D5 | NRRD file does not exist | Exit code ≠ 0, message "file not found"; no MP4 created |
| TC-D6 | CSV has an invalid plane | Exit code ≠ 0, message names the line; no MP4 created |
| TC-D7 | Wrong number of arguments | Exit code ≠ 0, usage message |
| TC-D8 | Real scan `MRHead.nrrd` + `examples/axial_sweep.csv` | Video plays; we check it by eye ([section 6.2](#62-visual-check-manual)) |
| TC-D9 | Output folder does not exist | Exit code ≠ 0, clear message, no traceback |
| TC-D10 | A plane with legs of 100,000 voxels | Exit code ≠ 0, "line 1 … too large", no traceback, no MP4 |
| TC-D11 | `--fps 0`, `--fps -5`, `--fps abc` | Exit code ≠ 0, message about `--fps` |

TC-D1 to TC-D7 and TC-D9 to TC-D11 use the small synthetic files, so they run in under a second.

---

## 6. Performance and visual checks

### 6.1 Performance (NFR-1)

| ID | Setup | Pass if |
| --- | --- | --- |
| TC-F1 | Random 500³ uint8 volume, 100 rotating planes of about 500×500 pixels | **≥ 30 FPS** (target ≥ 100) |
| TC-F2 | `CTACardio` (512×512×321), 100 planes | ≥ 30 FPS |

We record the machine (CPU, Python version) with every result.

### 6.2 Visual check (manual)

For each real scan we render three videos (axial sweep, rotating plane,
triangles) and check:
- the anatomy is where we expect it (eyes at the front, cerebellum at the back),
- the image does not jump or flicker between frames (FR-11),
- nothing is mirrored or upside down compared to 3D Slicer's views.

---

## 7. Traceability: requirement → tests

| Requirement | Test cases |
| --- | --- |
| FR-1 Load NRRD | TC-IO1, TC-D1 |
| FR-2 8/16/32 bit, signed and unsigned | TC-J11, TC-IO1 |
| FR-3 Reject non-3D / bad size | TC-IO2 |
| FR-4 3-point plane | TC-P1, TC-P2, TC-P3 |
| FR-5 4-point plane | TC-P6, TC-P7, TC-P8, TC-P10, TC-P11 |
| FR-6 Clear error for invalid plane | TC-P3–TC-P13, TC-IO5, TC-D6 |
| FR-7 Projection algorithm | TC-J1–TC-J8, TC-J12 |
| FR-8 Outside → 0 | TC-J9, TC-J10 |
| FR-9 Read CSV | TC-IO3–TC-IO6, TC-IO8–TC-IO10, TC-IO12 |
| FR-10 MP4, one frame per plane, in order | TC-IO7, TC-D1, TC-D2, TC-D4 |
| FR-11 Same brightness scale for all frames | TC-D8, [section 6.2](#62-visual-check-manual) |
| FR-12 Plane size limit | TC-P12, TC-P13, TC-D10 |
| FR-13 Output path checked | TC-IO11, TC-D9 |
| NFR-1 Performance | TC-F1, TC-F2 |
| NFR-2 Axis-aligned = slice | TC-J1 |
| NFR-3 Robustness | TC-J9, TC-D5–TC-D7, TC-D9–TC-D11 |
| NFR-4 Separate modules | Code review, [DESIGN.md](DESIGN.md), TC-P14 |
| NFR-5 Every FR tested | This table |
| NFR-6 Portability | Running the tests on macOS and Linux |

---

## 8. When is a change "done"?

- All automated tests pass (`python -m pytest`).
- The benchmark still meets TC-F1.
- A new feature or bug fix comes with a new test case in this document and in `tests/`.
