# Spinning Cube & Donut

A 3D ASCII renderer with two scenes and three implementations:

* **🐍 Python (terminal)** — the original, runs in your terminal. Zero
  dependencies. Two scripts: `cube.py` and `donut.py`.
* **⚛️ Browser (cube)** — `frontend/` — a Vite + React + TypeScript +
  TailwindCSS port of the cube, with sliders for speed, pause, reset.
* **⚛️ Browser (donut)** — `frontend-donut/` — same stack, ported from
  `donut.py`, with the same controls.

Both scenes use a 16-character brightness ramp:

```
 .'`,:;-+=*#%@$
```

Inspired by Andy Sloane's classic `donut.c` from the 2006 demoscene.

## Quick start

### Python (terminal)

```bash
python cube.py     # spinning cube
python donut.py    # spinning donut
```

* **Linux / macOS** — uses `curses` for smooth full-screen animation
  (press `q` or `ESC` to quit).
* **Windows** — uses ANSI escape sequences (Ctrl+C to quit).

Both scripts accept the same options:

* `--width N` / `--height N` — override the buffer size (plain mode).
* `--once` — render a single static frame and exit.
* `--spins K` — with `--once`, rotate K full turns around the Y axis.

Requires Python 3.8+. No third-party packages.

### Browser

```bash
# Cube
cd frontend
npm install
npm run dev          # http://localhost:5173

# Donut
cd ../frontend-donut
npm install
npm run dev          # http://localhost:5173 (different port if 5173 is busy)
```

Each frontend is a self-contained Vite project. Run them in two
separate terminals to view the cube and donut side-by-side.

Requires Node.js 18+ and npm.

## Features

The renderer ships with **two ASCII scenes** — the cube and the
donut — both using the same Phong lighting pipeline and the same
16-character shade ramp:

**Cube** — The same renderer as the Python version. Each visible face
is triangulated and rasterised with a per-pixel z-buffer and Gouraud
per-vertex normal interpolation. Back-face culled so only the three
front faces are drawn.

**Donut** — A parametric torus (major radius 1.0, tube radius 0.4)
rendered using the classic donut.c algorithm: a ring of 90 points swept
through 24 angular steps, with analytic surface normals. Same z-buffer,
shading, and Phong lighting as the cube.

Both share:

* **3D rotation** around the X and Y axes every frame.
* **Perspective projection** with aspect-ratio compensation (terminal
  characters are ~2× taller than wide, so the Y axis is scaled by 0.5).
* **Phong-style lighting**: a key directional light, a softer fill from
  the opposite side, and a tight specular highlight (`keyDot ** 8`).
* **Per-pixel z-buffer** for correct surface overlap and occlusion.
* **Depth falloff** that gently dims the scene as it moves away from
  the camera — a touch of atmospheric perspective.
* **Aspect-ratio-aware sizing** that fills the available space.

The browser frontends add:

* Live X / Y rotation-speed sliders.
* `pause`, `reset`, and `help` controls in the header.
* Auto-resizing character grid that fits the browser window via
  `ResizeObserver`.
* Subtle CRT-style text shadow and a dark terminal theme.

## Project layout

```
.
├── cube.py                # Python cube renderer + animation loop
├── donut.py               # Python donut renderer + animation loop
├── demo.py                # Writes 5 static demo frames to .txt files
├── demo_*.txt             # Pre-rendered preview frames (cube + donut)
├── README.md              # This file
├── frontend/              # Browser port of the cube
│   ├── src/
│   │   ├── main.tsx
│   │   ├── App.tsx
│   │   ├── CubeView.tsx
│   │   ├── renderer.ts
│   │   ├── Github.tsx
│   │   └── index.css
│   ├── index.html
│   ├── package.json
│   ├── tailwind.config.js
│   ├── vite.config.ts
│   └── tsconfig*.json
└── frontend-donut/        # Browser port of the donut (same structure)
    ├── src/
    │   ├── main.tsx
    │   ├── App.tsx
    │   ├── CubeView.tsx
    │   ├── donutRenderer.ts
    │   ├── Github.tsx
    │   └── index.css
    ├── index.html
    ├── package.json
    ├── tailwind.config.js
    ├── vite.config.ts
    └── tsconfig*.json
```

## Python command-line options

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

`demo.py` writes five static frames to text files — four of the cube
from different angles, plus one of the donut:

```
python demo.py
# -> demo_front.txt, demo_angle.txt, demo_side.txt, demo_top.txt, demo_donut.txt
```

These give a quick preview of how the animation looks from different
angles without having to launch the full animation loop.

## Tweaking the renderer

The render algorithm is intentionally compact and easy to play with.

### Cube (`cube.py` and `frontend/src/renderer.ts`)

* **Brightness ramp** — edit the `SHADE_CHARS` string to remap shading.
  More characters give a smoother gradient; fewer give a chunky look.
* **Lighting weights** — adjust the `0.16` (ambient), `0.62` (key),
  `0.15` (fill), and `0.18` (specular) constants in `shade_char()`.
* **Specular tightness** — change `keyDot ** 8` to `** 4` for a broad
  highlight, or `** 32` for a tight pinprick of light.
* **Light direction** — tweak the `LIGHT` vector to move the highlight.
* **Projection scale** — the `0.55` constant in `project()` controls
  how big the cube appears.
* **Aspect ratio** — the `* 0.5` Y-scale compensates for tall terminal
  characters. Change or remove it for a stretched look.

### Donut (`donut.py` and `frontend/src/donutRenderer.ts`)

* **Torus size** — the `R` and `r` constants control the major (ring)
  and minor (tube) radii. Try `R=1.5, r=0.25` for a thinner hoop, or
  `R=0.8, r=0.5` for a fatter shape.
* **Surface smoothness** — `A_STEPS` and `B_STEPS` control the angular
  subdivision. Bump to `180/48` for buttery-smooth tubes, or drop to
  `45/12` for a more pixelated retro look.
* **Distance** — the `distance` constant in `render()` changes the
  field of view (smaller = wider-angle / more fisheye).

## License

MIT. Inspired by `donut.c` (Andy Sloane, 2006).
