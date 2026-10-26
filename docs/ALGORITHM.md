# The Projection Algorithm

This document defines, in detail, how a plane is turned into a 2D image.
It covers requirement **FR-7** of the [SRS](SRS.md).

---

## 1. Input and output

**Input**
- A volume `M` of size `sx × sy × sz`.
- A plane, given as an isosceles triangle `(a, b, c)` with `dist(a,b) = dist(a,c)`.
  (The 4-point trapezoid is handled in §6.)

**Output**
- A 2D image `E` with `H` rows and `W` columns:
  - `Dab = dist(a,b)` (length of a leg), `Dbc = dist(b,c)` (length of the base)
  - `H = ceil(Dab)`, the rows `y = 0 … H−1`
  - `W = floor(Dbc) + 1`, the columns `x = 0 … W−1`
- `a` is at the top of the image and the base `b–c` is the bottom row.

---

## 2. The course algorithm (as given)

```
1. Dab = dist(a,b) = dist(a,c);  Dbc = dist(b,c)
2. v(ab) = (b − a) / Dab;  v(ac) = (c − a) / Dab        # unit vectors along the legs
3. E = new matrix [Dab × Dbc]
4. a1 = a;  a2 = a
5. for y = 0 … Dab−1:
     a1 = a1 + v(ab)                                    # step down the left leg
     a2 = a2 + v(ac)                                    # step down the right leg
     p  = a1
     d12 = dist(a1, a2)                                 # length of this row
     dp  = (a2 − a1) / d12                              # unit vector along the row
     for x1 = 0 … d12:
         v = M[p]          (0 if p is outside M)
         x = Dbc/2 − d12/2 + x1                         # centre the row
         E[x][y] = v
         p = p + dp
6. return E
```

**In words:** two walkers start at `a` and step down the two legs, one unit
per step. After every step, the segment between them is one row of the image.
We walk along that segment one unit at a time, read the volume at each point,
and write the value into the image, centred.

---

## 3. What the course algorithm leaves open, and our decisions

The assignment says the problem is "not well-defined". These are the gaps
we found and how we close them:

| # | Open question | Decision |
| --- | --- | --- |
| 1 | `p` has fractional coordinates (e.g. `(2.4, 0.8, 0)`). Which voxel do we read? | The **nearest voxel**: round each coordinate (`floor(v + 0.5)`). |
| 2 | `x = Dbc/2 − d12/2 + x1` is fractional (e.g. 2.4). Which column gets the value? | Avoided by design: we go over whole columns (pixels) instead, see §4. |
| 3 | Because of that fraction, rounding can shift a row up to half a pixel to one side, so rows are not exactly centred. | A pixel is filled exactly when its centre lies inside the triangle, so every row is symmetric around the image centre. |
| 4 | Is the apex `a` itself sampled? | No. The algorithm steps first, so row `y` is at distance `y + 1` from `a`. |
| 5 | `E[x][y]` or `E[y][x]`? | We store `E[y][x]` (row, column), the usual convention for images. |
| 6 | Image size when `Dab`, `Dbc` are not integers. | `H = ceil(Dab)`, `W = floor(Dbc) + 1` (see §1). |
| 7 | Pixels outside the triangle. | Value 0 (black). |
| 8 | Points outside the volume. | Value 0 (black), as the assignment says. |

---

## 4. Our formulation: "pull" instead of "push"

The course algorithm **pushes**: it walks along the plane and asks
*"where in the image does this point go?"*

We **pull**: for every pixel of the image we ask
*"where in the volume does this pixel come from?"*

### 4.1 Derivation
For row `y`, the walkers are at

```
a1(y) = a + (y+1)·v(ab)
a2(y) = a + (y+1)·v(ac)
```

Let `mid(y) = (a1 + a2) / 2` be the middle of the row and `dp = (a2 − a1) / d12`.

The course algorithm puts the sample `p = a1 + x1·dp` at column
`x = Dbc/2 − d12/2 + x1`. Solving for `x1` and substituting:

```
x1 = x − Dbc/2 + d12/2
p  = a1 + (x − Dbc/2 + d12/2)·dp
   = mid(y) + (x − Dbc/2)·dp
```

So **the 3D source of pixel (x, y) is**

```
P(x, y) = mid(y) + (x − Dbc/2) · dp
```

and the pixel is inside the triangle when its centre is within the row:

```
|x − Dbc/2| ≤ d12(y) / 2
```

### 4.2 Pseudo-code

```
for each row y = 0 … H−1:
    a1, a2 = a + (y+1)·v(ab),  a + (y+1)·v(ac)
    mid, d12, dp = (a1+a2)/2,  dist(a1,a2),  (a2−a1)/d12
    for each column x = 0 … W−1:
        if |x − Dbc/2| > d12/2:            E[y][x] = 0;  continue   # outside the triangle
        P = round(mid + (x − Dbc/2)·dp)                             # nearest voxel
        E[y][x] = M[P] if P is inside M else 0
```

### 4.3 Why this is better
1. **Well-defined and symmetric:** each pixel is computed exactly once, and a pixel is filled exactly when its centre is inside the triangle. No fractional columns to round.
2. **Fast:** the inner computation is the same formula for every pixel, so all
   pixels can be computed **at once** with array operations (NumPy) instead of
   a Python loop per pixel. This is what makes NFR-1 (30+ FPS) reachable in Python.
3. **Same result:** the formula is derived directly from the course algorithm,
   so the sampled points lie on the same rows.

---

## 5. Worked example

One flat layer (`z = 0`), triangle `a = (3,0,0)`, `b = (0,4,0)`, `c = (6,4,0)`.

- `Dab = 5`, `Dbc = 6` → image of `H = 5` rows × `W = 7` columns
- `v(ab) = (−0.6, 0.8, 0)`, `v(ac) = (0.6, 0.8, 0)`, `dp = (1, 0, 0)` for every row

| Row y | a1 | a2 | d12 | Filled columns (`\|x−3\| ≤ d12/2`) | Voxels read |
| --- | --- | --- | --- | --- | --- |
| 0 | (2.4, 0.8) | (3.6, 0.8) | 1.2 | 3 | (3,1) |
| 1 | (1.8, 1.6) | (4.2, 1.6) | 2.4 | 2, 3, 4 | (2,2) (3,2) (4,2) |
| 2 | (1.2, 2.4) | (4.8, 2.4) | 3.6 | 2, 3, 4 | (2,2) (3,2) (4,2) |
| 3 | (0.6, 3.2) | (5.4, 3.2) | 4.8 | 1 … 5 | (1,3) … (5,3) |
| 4 | (0, 4) | (6, 4) | 6.0 | 0 … 6 | (0,4) … (6,4) |

Resulting image (`■` = value read from the volume, `·` = 0):

```
· · · ■ · · ·
· · ■ ■ ■ · ·
· · ■ ■ ■ · ·
· ■ ■ ■ ■ ■ ·
■ ■ ■ ■ ■ ■ ■
```

Rows 1 and 2 read the same voxels because `1.6` and `2.4` both round to `2`.
This is expected with nearest-voxel sampling when a step is smaller than one voxel.

---

## 6. Trapezoid (4 points)

For `(a1, a2, b, c)` the same algorithm runs with one change: the left walker
starts at `a1` and the right walker at `a2` (instead of both at `a`).
The legs are `a1→b` and `a2→c`, with `Dab = dist(a1,b) = dist(a2,c)`.
If `dist(a1,a2) = dist(b,c)`, every row has the same length and the image is a
full rectangle.

---

## 7. Edge cases

| Case | Behaviour |
| --- | --- |
| Plane partly outside the volume | Outside points are 0; the rest is drawn normally. |
| Plane completely outside the volume | An all-black image (no error). |
| Plane not isosceles, or points on one line | Rejected before projecting (FR-6). |
| Very thin triangle (short base) | Some rows may have no pixel centre inside them; they stay black. |

---

## 8. Complexity

- **Time:** `O(H · W)` per plane: one formula and one lookup per pixel.
- **Memory:** `O(H · W)` for the image and temporary arrays. The volume is
  not copied.
