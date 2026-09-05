# Spinning Donut — Frontend

A browser port of the Python `donut.py` renderer, built with
**Vite + React + TypeScript + TailwindCSS**.

The renderer is a faithful line-by-line port of the Python version —
the same `SHADE_CHARS` ramp, the same Phong-style lighting (key + fill
+ specular), the same z-buffer for proper face overlap, the same
analytic surface normals on a parametric torus. It just runs in a
`<pre>` element in the browser.

The cube version of this app lives in the sibling `frontend/`
folder.

## Quick start

```bash
npm install
npm run dev          # http://localhost:5173 (opens automatically)
npm run build        # production build to dist/
npm run preview      # preview the production build
npm run lint         # run eslint
```

## Project layout

```
src/
  main.tsx            – React entry point
  App.tsx             – Top-level layout: header, donut view, controls, footer
  CubeView.tsx        – Canvas-ish component that runs the render loop
  donutRenderer.ts    – Pure-TS port of donut.py's render() function
  index.css           – Tailwind directives + .cube-output style
```

## How the renderer works

`donutRenderer.ts` exposes a `createDonutRenderer()` factory. Each
call to `state.render(ax, ay)`:

1. Iterates over a 90×24 grid of (A, B) surface points on the torus.
2. Computes the rotated 3D position for each point.
3. Computes the rotated analytic normal `(cosA·cosB, cosA·sinB, sinA)`.
4. Projects both to 2D with perspective and an aspect-ratio correction.
5. Culls back-facing points (those facing away from the camera).
6. For each visible point, shades it with key+fill+specular and writes
   the resulting character if it passes the per-pixel z-buffer test.

The output is an array of strings (one per row). The view component
joins them with `\n` and writes them to a `<pre>` element.

## Tweaking

* **Brightness ramp** — edit `SHADE_CHARS` in `src/donutRenderer.ts`.
* **Lighting weights** — edit the magic numbers (`0.16`, `0.62`,
  `0.15`, `0.18`) inside the `shadeChar` function in
  `src/donutRenderer.ts`.
* **Mesh resolution** — edit `A_STEPS` (90) and `B_STEPS` (24) in
  `src/donutRenderer.ts`. Higher = smoother, slower.
* **Torus shape** — edit the `R` (major radius) and `r` (tube radius)
  constants in `src/donutRenderer.ts`.
* **Style** — colors, fonts, layout all live in `src/index.css` and
  inline Tailwind classes in `App.tsx` / `CubeView.tsx`.
