# Demo Runs: Good, Edge and Bad Cases

Full output of `bash run_demo_cases.sh` (see [EXPERIMENT.md](EXPERIMENT.md) §4 for the summary).
Run it yourself from the project folder, with the virtual environment active:

```
bash run_demo_cases.sh
```

```text
######## GOOD RUNS ########

==================================================================
  G1  rotating plane (90 rectangles)
==================================================================
$ python Ex0.py data/MRHead.nrrd examples/rotating.csv results/cases/G1_rotating.mp4
volume: (256, 256, 130) int16, planes: 90
projected 90 planes in 0.028 s (3213 per second)
wrote results/cases/G1_rotating.mp4
-> exit code 0

==================================================================
  G2  axial sweep, top of head to neck
==================================================================
$ python Ex0.py data/MRHead.nrrd examples/axial_sweep.csv results/cases/G2_axial_sweep.mp4
volume: (256, 256, 130) int16, planes: 120
projected 120 planes in 0.039 s (3107 per second)
wrote results/cases/G2_axial_sweep.mp4
-> exit code 0

==================================================================
  G3  triangles (3-point planes)
==================================================================
$ python Ex0.py data/MRHead.nrrd examples/triangles.csv results/cases/G3_triangles.mp4
volume: (256, 256, 130) int16, planes: 40
projected 40 planes in 0.013 s (3115 per second)
wrote results/cases/G3_triangles.mp4
-> exit code 0

==================================================================
  G4  also save every frame as PNG
==================================================================
$ python Ex0.py data/MRHead.nrrd examples/edge/mixed_shapes.csv results/cases/G4_mixed.mp4 --png-dir results/cases/G4_png
volume: (256, 256, 130) int16, planes: 2
projected 2 planes in 0.001 s (1945 per second)
wrote results/cases/G4_mixed.mp4
wrote 2 PNG files to results/cases/G4_png
-> exit code 0

==================================================================
  G5  help
==================================================================
$ python Ex0.py --help
usage: Ex0.py [-h] [--fps FPS] [--png-dir PNG_DIR] nrrd csv mp4

Demo: cut a 3D volume along a list of planes and save the cuts as a video.

Usage:
    python Ex0.py <file.nrrd> <file.csv> <file.mp4> [--fps 10] [--png-dir DIR]

    file.nrrd  the 3D volume
    file.csv   one plane per line: 9 numbers (a, b, c) or 12 (a1, a2, b, c)
    file.mp4   the output video, one frame per plane, in CSV order

positional arguments:
  nrrd               3D volume (NRRD)
  csv                list of planes (CSV)
  mp4                output video (MP4)

options:
  -h, --help         show this help message and exit
  --fps FPS          frames per second in the video (default 10)
  --png-dir PNG_DIR  also save every frame as a PNG in this folder
-> exit code 0

######## EDGE CASES (valid input, unusual result) ########

==================================================================
  E1  triangle and rectangle in one CSV
==================================================================
$ python Ex0.py data/MRHead.nrrd examples/edge/mixed_shapes.csv results/cases/E1_mixed.mp4
volume: (256, 256, 130) int16, planes: 2
projected 2 planes in 0.001 s (2027 per second)
wrote results/cases/E1_mixed.mp4
-> exit code 0

==================================================================
  E2  plane half outside the scan
==================================================================
$ python Ex0.py data/MRHead.nrrd examples/edge/partly_outside.csv results/cases/E2_partly_outside.mp4
volume: (256, 256, 130) int16, planes: 1
projected 1 planes in 0.001 s (1543 per second)
wrote results/cases/E2_partly_outside.mp4
-> exit code 0

==================================================================
  E3  plane completely outside the scan
==================================================================
$ python Ex0.py data/MRHead.nrrd examples/edge/fully_outside.csv results/cases/E3_fully_outside.mp4
volume: (256, 256, 130) int16, planes: 1
projected 1 planes in 0.001 s (1548 per second)
wrote results/cases/E3_fully_outside.mp4
-> exit code 0

######## BAD INPUT (must fail with a clear message, no video) ########

==================================================================
  B1  plane is not isosceles
==================================================================
$ python Ex0.py data/MRHead.nrrd examples/bad/not_isosceles.csv results/cases/B1.mp4
error: examples/bad/not_isosceles.csv, line 3: legs differ in length: 263.0309 vs 264.5170 (EPS = 0.001)
-> exit code 2

==================================================================
  B2  three points on one line
==================================================================
$ python Ex0.py data/MRHead.nrrd examples/bad/collinear.csv results/cases/B2.mp4
error: examples/bad/collinear.csv, line 2: a, b, c are collinear (on one line), so they do not define a plane
-> exit code 2

==================================================================
  B3  four points not on one plane
==================================================================
$ python Ex0.py data/MRHead.nrrd examples/bad/not_coplanar.csv results/cases/B3.mp4
error: examples/bad/not_coplanar.csv, line 2: the four points are not on the same plane
-> exit code 2

==================================================================
  B4  trapezoid top wider than base
==================================================================
$ python Ex0.py data/MRHead.nrrd examples/bad/top_wider.csv results/cases/B4.mp4
error: examples/bad/top_wider.csv, line 2: dist(a1, a2) must be <= dist(b, c)
-> exit code 2

==================================================================
  B5  wrong count of numbers
==================================================================
$ python Ex0.py data/MRHead.nrrd examples/bad/wrong_count.csv results/cases/B5.mp4
error: examples/bad/wrong_count.csv, line 2: expected 9 or 12 numbers, got 7
-> exit code 2

==================================================================
  B6  a word instead of a number
==================================================================
$ python Ex0.py data/MRHead.nrrd examples/bad/not_a_number.csv results/cases/B6.mp4
error: examples/bad/not_a_number.csv, line 3: not a number in ['0', '128', 'abc', '255', '128', '0', '255', '128', '129']
-> exit code 2

==================================================================
  B7  CSV without planes
==================================================================
$ python Ex0.py data/MRHead.nrrd examples/bad/empty.csv results/cases/B7.mp4
error: examples/bad/empty.csv: no planes found
-> exit code 2

==================================================================
  B8  NRRD file does not exist
==================================================================
$ python Ex0.py data/missing.nrrd examples/rotating.csv results/cases/B8.mp4
error: data/missing.nrrd: file not found
-> exit code 2

==================================================================
  B9  CSV file does not exist
==================================================================
$ python Ex0.py data/MRHead.nrrd examples/missing.csv results/cases/B9.mp4
error: examples/missing.csv: file not found
-> exit code 2

==================================================================
  B10 a file that is not NRRD
==================================================================
$ python Ex0.py README.md examples/rotating.csv results/cases/B10.mp4
error: README.md: not a valid NRRD file (Invalid NRRD magic line. Is this an NRRD file?)
-> exit code 2

==================================================================
  B11 missing arguments
==================================================================
$ python Ex0.py data/MRHead.nrrd
usage: Ex0.py [-h] [--fps FPS] [--png-dir PNG_DIR] nrrd csv mp4
Ex0.py: error: the following arguments are required: csv, mp4
-> exit code 2

######## videos that were created ########
results/cases/E1_mixed.mp4
results/cases/E2_partly_outside.mp4
results/cases/E3_fully_outside.mp4
results/cases/G1_rotating.mp4
results/cases/G2_axial_sweep.mp4
results/cases/G3_triangles.mp4
results/cases/G4_mixed.mp4
```
