# Spinning Cube

An iconic 3D spinning cube rendered in pure Python using ASCII characters.
No third-party libraries, no graphics libraries — just the standard library.

A **Vite + React + TypeScript + TailwindCSS** port is also available in
[`frontend/`](./frontend/) that runs the same renderer in the browser.

Inspired by Andy Sloane's classic `donut.c` from the 2006 demoscene.

## What it does

* Defines the 8 vertices and 6 faces of a cube.
* Applies 3D rotation (around the X and Y axes) every frame.
* Projects 3D points to 2D using perspective division with
  aspect-ratio compensation (terminal chars are ~2× taller than wide,
  so the Y axis is scaled by 0.5 to make the cube look like a cube,
  not a stretched pillar).
* Rasterizes each visible face as two triangles using barycentric
  coordinates and a per-pixel z-buffer for proper depth ordering.
* Uses **per-vertex normal interpolation** so each face shows a smooth
  gradient from corner to corner (Gouraud-style shading).
* Shades each pixel with a Lambertian dot-product against a key
  directional light, plus a soft fill light from the opposite side,
  mapped onto a 16-character brightness ramp:
  ` .'`,:;-+=*#%@$`.
* **Back-face culling** skips faces pointing away from the camera.

The result is a smoothly-rotating, lit cube that fills the terminal.

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

## Frontend (browser)

A web port lives in [`frontend/`](./frontend/). It uses the same ASCII
renderer, ported line-by-line to TypeScript, and renders to a `<pre>`
element styled with TailwindCSS.

```bash
cd frontend
npm install
npm run dev      # opens http://localhost:5173
npm run build    # production build to dist/
```

Features:

* Same Phong-style lighting, per-vertex normals, and z-buffer as the
  Python version.
* Live X / Y rotation speed sliders in the footer.
* `pause`, `reset`, and `help` buttons in the header.
* Auto-resizes the character grid to fit the browser window.

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
