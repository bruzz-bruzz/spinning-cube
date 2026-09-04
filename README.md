# Spinning Cube

An iconic 3D spinning cube rendered in pure Python using ASCII characters.
No third-party libraries, no graphics libraries — just the standard library.

Inspired by Andy Sloane's classic `donut.c` from the 2006 demoscene.

## What it does

* Defines the 8 vertices and 6 faces of a cube.
* Applies 3D rotation (around the X and Y axes) every frame.
* Projects 3D points to 2D using simple perspective division.
* Rasterizes each visible face as two triangles using barycentric
  coordinates and a per-pixel z-buffer.
* Shades each face with a Lambertian dot-product against a fixed
  directional light, mapping brightness onto a ramp of characters:
  `.:-=+*#%@`.

The result is a smoothly-rotating, lit cube that fits in any terminal.

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
```

## Demo frames

`demo.py` writes four static frames of the rotating cube to text files:

```
python demo.py
# -> demo_front.txt, demo_angle.txt, demo_side.txt, demo_top.txt
```

These give a quick preview of how the animation looks from different
angles without having to launch the full animation loop.
