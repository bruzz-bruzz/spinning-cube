# Spinning Cube

An iconic 3D spinning cube rendered in **pure ASCII characters**, with
two implementations sharing the same shading algorithm:

* **🐍 Python** — the original, runs in your terminal. Zero dependencies.
* **⚛️ Browser** — a Vite + React + TypeScript + TailwindCSS port with
  a control panel for speed, pause, and reset.

Both produce the same lit, smoothly-rotating cube from a 16-character
brightness ramp:

```
 .'`,:;-+=*#%@$
```

Inspired by Andy Sloane's classic `donut.c` from the 2006 demoscene.

## Quick start

### Python (terminal)

```bash
python cube.py
```

* **Linux / macOS** — uses `curses` for smooth full-screen animation
  (press `q` or `ESC` to quit).
* **Windows** — uses ANSI escape sequences (Ctrl+C to quit).

Requires Python 3.8+. No third-party packages.

### Browser

```bash
cd frontend
npm install
npm run dev          # http://localhost:5173
npm run build        # production build to dist/
```

Requires Node.js 18+ and npm.

## Features

Both versions share the same render pipeline:

* **3D rotation** around the X and Y axes every frame.
* **Perspective projection** with aspect-ratio compensation — terminal
  characters are ~2× taller than wide, so the Y axis is scaled by 0.5
  to make the cube look like a cube instead of a stretched pillar.
* **Per-vertex normal interpolation** (Gouraud-style) so each face shows
  a smooth gradient from corner to corner.
* **Phong-style lighting**: a key directional light (`(0.5, 0.5, -1.0)`),
  a softer fill from the opposite side, and a tight specular highlight
  (`keyDot ** 8`) for that shiny plastic look.
* **Per-pixel z-buffer** for correct face overlap, plus **back-face
  culling** to skip faces pointing away from the camera.
* **Depth falloff** that gently dims the cube as it moves away from the
  camera — a touch of atmospheric perspective.
* **Aspect-ratio-aware sizing** that fills the available space
  (terminal rows × cols, or browser window) without distorting the cube.

The browser version adds:

* Live X / Y rotation-speed sliders.
* `pause`, `reset`, and `help` controls in the header.
* Auto-resizing character grid that fits the browser window via
  `ResizeObserver`.
* Subtle CRT-style text shadow and a dark terminal theme.

## Project layout

```
.
├── cube.py             # Python renderer + animation loop
├── demo.py             # Writes 4 static demo frames to .txt files
├── demo_*.txt          # Pre-rendered preview frames
├── README.md           # This file
└── frontend/           # Browser port
    ├── src/
    │   ├── main.tsx    # React entry point
    │   ├── App.tsx     # Top-level layout
    │   ├── CubeView.tsx# Render-loop React component
    │   ├── renderer.ts # Pure-TS port of cube.py's render()
    │   └── index.css   # Tailwind directives
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

`demo.py` writes four static frames of the rotating cube to text files:

```
python demo.py
# -> demo_front.txt, demo_angle.txt, demo_side.txt, demo_top.txt
```

These give a quick preview of how the animation looks from different
angles without having to launch the full animation loop.

## Tweaking the renderer

The render algorithm is intentionally compact and easy to play with.
Knobs to try (in both `cube.py` and `frontend/src/renderer.ts`):

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

## License

MIT. Inspired by `donut.c` (Andy Sloane, 2006).
