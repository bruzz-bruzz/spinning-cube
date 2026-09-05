# Spinning Cube

An iconic 3D spinning cube rendered in pure Python using ASCII characters.
No third-party libraries, no graphics libraries — just the standard library.

Inspired by Andy Sloane's classic `donut.c` from the 2006 demoscene.

## What it does

* Defines the 8 vertices and 6 faces of a cube.
* Applies 3D rotation (around the X and Y axes) every frame.
* Projects 3D points to 2D using perspective division with aspect-ratio
  compensation (so the cube looks like a cube, not a tall pillar).
* Rasterizes each visible face as two triangles using barycentric
  coordinates and a per-pixel z-buffer for proper depth ordering.
* Computes per-vertex normals (averaged from adjacent face normals) and
  interpolates them across each face for **smooth Gouraud-style shading**.
* Shades each pixel with a Lambertian dot-product against a directional
  light, mapping brightness onto a ramp of characters: ` .,:;-+=!*#%@`.
* **Optional ANSI true-color (24-bit)** per face - each of the 6 faces has
  its own base color and the shade characters pick the brightness within
  that color, making the cube pop on any modern terminal.
* **Edge enhancement** detects silhouette pixels and uses the brightest
  character for crisp, clean outlines.
* **Back-face culling** skips faces pointing away from the camera.

The result is a smoothly-rotating, lit, colorized cube that fits in any
terminal.

## Running

```bash
python cube.py
```

On Linux/macOS the script uses `curses` for smooth full-screen animation
(press `q` or `ESC` to quit). On Windows — where `curses` is not part of
the standard distribution — it falls back to writing ANSI-escape sequences
to stdout (Ctrl+C to quit).

## Requirements

* Python 3.8 or newer.
* No third-party packages.
* A terminal that supports ANSI 24-bit true color (Windows 10+ Terminal,
  iTerm2, gnome-terminal, etc.) for the colored version. With
  `USE_COLOR = False` the cube works in any terminal.

## Command-line options

```
python cube.py [--width N] [--height N] [--once] [--spins N]
```

* `--width N` / `--height N` — force the rendered frame size when running
  in plain (ANSI) mode. Useful when redirecting output to a file or piping
  into another program.
* `--once` — render a single frame and exit, instead of animating.
* `--spins N` — when used with `--once`, rotate the cube `N` full turns
  around the Y axis before rendering.

Examples:

```bash
# Animate full-screen
python cube.py

# Render one pretty frame to a text file
python cube.py --once --width 80 --height 24 --spins 0.25 > cube.txt

# Render a larger frame in full color (will include ANSI escape codes)
python cube.py --once --width 120 --height 40 --spins 0.2 > cube_color.txt
```

## Demo frames

`demo.py` writes four static frames of the rotating cube to text files:

```
python demo.py
# -> demo_front.txt, demo_angle.txt, demo_side.txt, demo_top.txt
```

These give a quick preview of how the animation looks from different
angles without having to launch the full animation loop.

## Configuration

You can tweak the look by editing the top of `cube.py`:

```python
SHADE_CHARS = " .,:;-+=!*#%@"   # Brightness ramp (dim -> bright)
USE_COLOR = True                 # Set to False for plain ASCII
FACE_COLORS = [                  # RGB per face (front, back, top, bottom, right, left)
    (255,  90,  90),   # -Z front    (warm red)
    ( 90,  90, 255),   # +Z back     (blue)
    (255, 230,  90),   # +Y top      (yellow)
    (130,  90, 255),   # -Y bottom   (purple)
    ( 90, 230,  90),   # +X right    (green)
    (255, 150,  90),   # -X left     (orange)
]
```

Set `USE_COLOR = False` to get plain ASCII output that looks the same on
any terminal (handy for piping to a file, embedding in a README, or
running on old terminals without 24-bit color support).

## Technical notes

* **Projection** — simple perspective with `factor = 1 / (z + distance)`.
  The scale factor accounts for terminal character aspect ratio (chars
  are roughly 2× taller than wide), so the cube is a cube and not a
  stretched pillar.
* **Lighting** — single directional light at `(0.6, 0.8, -0.2)`,
  upper-right-front, normalized. This gives strong contrast between
  faces and makes the rotation read clearly.
* **Shading** — per-vertex normals are the average of the three adjacent
  face normals. These are interpolated across each triangle and
  renormalized per pixel, giving a smooth gradient even on flat faces.
* **Depth** — a `zbuf` array stores the closest depth seen at each pixel.
  Only pixels closer than the existing value are written, so the painter's
  algorithm sort by average face depth produces correct overlap.
* **Color** — 24-bit ANSI escapes (`\x1b[38;2;R;G;Bm`) are emitted per
  character when `USE_COLOR` is `True`. Disable it for old terminals or
  when piping to a non-color-aware viewer.
* **Edges** — after the fill pass, pixels that border a large jump in
  brightness are upgraded to the brightest character, giving crisp
  silhouettes that read clearly even on the smallest terminal.
