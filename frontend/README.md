# Spinning Cube — Frontend

A browser port of the Python spinning-cube renderer, built with
**Vite + React + TypeScript + TailwindCSS**.

The renderer is a faithful line-by-line port of the Python version —
the same `SHADE_CHARS` ramp, the same Phong-style lighting (key + fill
+ specular), the same Gouraud per-vertex normal interpolation, and
the same z-buffer for proper face overlap. It just runs in a
`<pre>` element in the browser.

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
  main.tsx        – React entry point
  App.tsx         – Top-level layout: header, cube view, controls, footer
  CubeView.tsx    – Canvas-ish component that runs the render loop
  renderer.ts     – Pure-TS port of cube.py's render() function
  index.css       – Tailwind directives + .cube-output style
```

## How the renderer works

`renderer.ts` exposes a `createRenderer()` factory. Each call to
`state.render(ax, ay)`:

1. Rotates the 8 cube vertices around X then Y.
2. Projects them to 2D with perspective + aspect-ratio correction.
3. Culls back-facing triangles.
4. For each visible face, rasterises the two triangles using
   barycentric coordinates and a per-pixel z-buffer.
5. Interpolates per-vertex normals across the face, renormalises
   them, and maps the result to a shade character.

The output is an array of strings (one per row). The view component
joins them with `\n` and writes them to a `<pre>` element.

## Tweaking

* **Brightness ramp** — edit `SHADE_CHARS` in `src/renderer.ts`.
* **Lighting weights** — edit the `shadeChar` function in
  `src/renderer.ts`.
* **Projection scale** — edit the `0.55` constant in `project()`.
* **Style** — colors, fonts, layout all live in `src/index.css` and
  inline Tailwind classes in `App.tsx` / `CubeView.tsx`.
