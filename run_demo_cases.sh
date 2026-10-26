#!/usr/bin/env bash
# Runs the demo on every case a grader might try: good runs, edge cases and
# bad input. For each case it prints the command, the program's output and
# the exit code (0 = success, anything else = error).
#
# Usage (from the project folder, with the virtual environment active):
#     bash run_demo_cases.sh
#
# Needs: data/MRHead.nrrd  (python data/download_data.py MRHead)

PY="${PYTHON:-python}"
OUT="results/cases"
mkdir -p "$OUT"

run() {   # run "<title>" <arguments for Ex0.py...>
    local title="$1"; shift
    echo
    echo "=================================================================="
    echo "  $title"
    echo "=================================================================="
    echo "\$ python Ex0.py $*"
    "$PY" Ex0.py "$@"
    echo "-> exit code $?"
}

H=data/MRHead.nrrd

echo "######## GOOD RUNS ########"
run "G1  rotating plane (90 rectangles)"       $H examples/rotating.csv      $OUT/G1_rotating.mp4
run "G2  axial sweep, top of head to neck"     $H examples/axial_sweep.csv   $OUT/G2_axial_sweep.mp4
run "G3  triangles (3-point planes)"           $H examples/triangles.csv     $OUT/G3_triangles.mp4
run "G4  also save every frame as PNG"         $H examples/edge/mixed_shapes.csv $OUT/G4_mixed.mp4 --png-dir $OUT/G4_png
run "G5  help"                                 --help

echo
echo "######## EDGE CASES (valid input, unusual result) ########"
run "E1  triangle and rectangle in one CSV"    $H examples/edge/mixed_shapes.csv   $OUT/E1_mixed.mp4
run "E2  plane half outside the scan"          $H examples/edge/partly_outside.csv $OUT/E2_partly_outside.mp4
run "E3  plane completely outside the scan"    $H examples/edge/fully_outside.csv  $OUT/E3_fully_outside.mp4

echo
echo "######## BAD INPUT (must fail with a clear message, no video) ########"
run "B1  plane is not isosceles"               $H examples/bad/not_isosceles.csv $OUT/B1.mp4
run "B2  three points on one line"             $H examples/bad/collinear.csv     $OUT/B2.mp4
run "B3  four points not on one plane"         $H examples/bad/not_coplanar.csv  $OUT/B3.mp4
run "B4  trapezoid top wider than base"        $H examples/bad/top_wider.csv     $OUT/B4.mp4
run "B5  wrong count of numbers"               $H examples/bad/wrong_count.csv   $OUT/B5.mp4
run "B6  a word instead of a number"           $H examples/bad/not_a_number.csv  $OUT/B6.mp4
run "B7  CSV without planes"                   $H examples/bad/empty.csv         $OUT/B7.mp4
run "B8  NRRD file does not exist"             data/missing.nrrd examples/rotating.csv $OUT/B8.mp4
run "B9  CSV file does not exist"              $H examples/missing.csv           $OUT/B9.mp4
run "B10 a file that is not NRRD"              README.md examples/rotating.csv   $OUT/B10.mp4
run "B11 missing arguments"                    $H
run "B12 plane far too large"                  $H examples/bad/too_large.csv       $OUT/B12.mp4
run "B13 typo in the first line"               $H examples/bad/typo_first_line.csv $OUT/B13.mp4
run "B14 legs cross (not a trapezoid)"         $H examples/bad/legs_cross.csv      $OUT/B14.mp4
run "B15 output folder does not exist"         $H examples/rotating.csv            no_such_folder/out.mp4
run "B16 bad --fps"                            $H examples/rotating.csv            $OUT/B16.mp4 --fps 0

echo
echo "######## videos that were created ########"
ls -1 "$OUT"/*.mp4
