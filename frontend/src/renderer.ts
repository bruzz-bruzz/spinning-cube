/**
 * Spinning Cube — TypeScript port of the Python renderer.
 *
 * The original ASCII algorithm (in cube.py) is ported line-by-line so
 * the browser version renders the exact same cube as the terminal
 * version, just using JavaScript numbers and a string buffer instead
 * of Python.
 *
 * Public API:
 *   const state = createRenderer()
 *   state.resize(width, height)
 *   const rows = state.render(ax, ay)
 *
 * The renderer is stateless across calls; you pass the rotation angles
 * each frame and it returns the rendered output.
 */

// ---------------------------------------------------------------------------
// Geometry
// ---------------------------------------------------------------------------

/** Cube vertices (size 2, centered at origin). */
const CUBE_VERTICES: ReadonlyArray<readonly [number, number, number]> = [
  [-1, -1, -1], // 0
  [ 1, -1, -1], // 1
  [ 1,  1, -1], // 2
  [-1,  1, -1], // 3
  [-1, -1,  1], // 4
  [ 1, -1,  1], // 5
  [ 1,  1,  1], // 6
  [-1,  1,  1], // 7
]

/** Six faces (CCW winding when viewed from outside). */
const CUBE_FACES: ReadonlyArray<readonly [number, number, number, number]> = [
  [0, 3, 2, 1], // -Z front
  [5, 6, 7, 4], // +Z back
  [3, 7, 6, 2], // +Y top
  [4, 0, 1, 5], // -Y bottom
  [1, 2, 6, 5], // +X right
  [4, 7, 3, 0], // -X left
]

/** Brightness ramp: dim -> bright. More characters = smoother gradient. */
const SHADE_CHARS = " .'`,:;-+=*#%@$"

/** Pre-normalised key-light direction. */
const LIGHT: [number, number, number] = (() => {
  const v: [number, number, number] = [0.5, 0.5, -1.0]
  const len = Math.hypot(v[0], v[1], v[2])
  return [v[0] / len, v[1] / len, v[2] / len]
})()

// ---------------------------------------------------------------------------
// Math helpers
// ---------------------------------------------------------------------------

/** Rotate a 3D point around X then Y by ``ax`` and ``ay`` (radians). */
function rotate(
  p: readonly [number, number, number],
  ax: number,
  ay: number,
): [number, number, number] {
  const [x0, y0, z0] = p
  // Rotation around X (tilt).
  const cy = Math.cos(ax)
  const sy = Math.sin(ax)
  const y1 = y0 * cy - z0 * sy
  const z1 = y0 * sy + z0 * cy
  // Rotation around Y (spin).
  const cx = Math.cos(ay)
  const sx = Math.sin(ay)
  const x2 = x0 * cx + z1 * sx
  const z2 = -x0 * sx + z1 * cx
  return [x2, y1, z2]
}

/** Project a 3D point to 2D screen coordinates with simple perspective. */
function project(
  p: readonly [number, number, number],
  width: number,
  height: number,
  cubeSize = 2.0,
): [number, number, number] {
  const [x, y, z0] = p
  const distance = 4
  const z = z0 + distance
  const factor = 1 / z
  // Use min(width, height*2) so a wider terminal doesn't squash the
  // cube vertically. The 0.5 Y-scale corrects for terminal char aspect.
  const k = cubeSize * Math.min(width, height * 2) * 0.55
  const sx = Math.round(width / 2 + x * factor * k)
  const sy = Math.round(height / 2 - y * factor * k * 0.5)
  return [sx, sy, z]
}

/** Compute the (un-normalized) outward normal of a planar face. */
function faceNormal(
  face: readonly [number, number, number, number],
  vertices: ReadonlyArray<readonly [number, number, number]>,
): [number, number, number] {
  const v0 = vertices[face[0]]
  const v1 = vertices[face[1]]
  const v2 = vertices[face[2]]
  const ex = v1[0] - v0[0]
  const ey = v1[1] - v0[1]
  const ez = v1[2] - v0[2]
  const fx = v2[0] - v0[0]
  const fy = v2[1] - v0[1]
  const fz = v2[2] - v0[2]
  return [
    ey * fz - ez * fy,
    ez * fx - ex * fz,
    ex * fy - ey * fx,
  ]
}

/** Average the normals of the 3 faces that share ``vertexIdx``. */
function vertexNormal(
  vertexIdx: number,
  vertices: ReadonlyArray<readonly [number, number, number]>,
): [number, number, number] {
  let nx = 0
  let ny = 0
  let nz = 0
  for (const face of CUBE_FACES) {
    if (face.includes(vertexIdx)) {
      const fn = faceNormal(face, vertices)
      nx += fn[0]
      ny += fn[1]
      nz += fn[2]
    }
  }
  return [nx, ny, nz]
}

export type Vec3 = readonly [number, number, number]
export type Face = readonly [number, number, number, number]

export interface RendererState {
  width: number
  height: number
  resize(width: number, height: number): void
  render(ax: number, ay: number): string[]
}

export function createRenderer(
  initialWidth = 80,
  initialHeight = 24,
): RendererState {
  let width = initialWidth
  let height = initialHeight
  let buf: string[][] = []
  let zbuf: number[][] = []

  function resize(w: number, h: number): void {
    width = w
    height = h
    buf = Array.from({ length: h }, () => new Array(w).fill(' '))
    zbuf = Array.from({ length: h }, () => new Array(w).fill(-1e9))
  }

  resize(initialWidth, initialHeight)

  /**
   * Map a (normalized) normal and depth to a shade character.
   * Uses key + fill + specular lighting (Phong-style).
   */
  function shadeChar(nx: number, ny: number, nz: number, z: number): string {
    const keyDot = nx * LIGHT[0] + ny * LIGHT[1] + nz * LIGHT[2]
    const key = Math.max(0, keyDot)
    const fill = Math.max(0, -nx * 0.4 + -ny * 0.4 + -nz * 0.2)
    const specular = keyDot > 0 ? Math.pow(keyDot, 8) : 0
    const depthFactor = 1 - Math.max(0, Math.min(0.15, (z - 3) * 0.04))
    const b =
      (0.16 + 0.62 * key + 0.15 * fill + 0.18 * specular) * depthFactor
    const idx = Math.min(
      SHADE_CHARS.length - 1,
      Math.max(0, Math.floor(b * SHADE_CHARS.length)),
    )
    return SHADE_CHARS[idx]
  }

  /** Rasterize a triangle with per-pixel shading (Gouraud-style). */
  function drawTriangle(
    p0: Vec3,
    p1: Vec3,
    p2: Vec3,
    n0: Vec3,
    n1: Vec3,
    n2: Vec3,
  ): void {
    const [x0, y0, z0] = p0
    const [x1, y1, z1] = p1
    const [x2, y2, z2] = p2

    const minX = Math.max(0, Math.min(x0, x1, x2))
    const maxX = Math.min(width - 1, Math.max(x0, x1, x2))
    const minY = Math.max(0, Math.min(y0, y1, y2))
    const maxY = Math.min(height - 1, Math.max(y0, y1, y2))
    if (minX > maxX || minY > maxY) return

    const edge = (a: Vec3, b: Vec3, c: Vec3): number =>
      (c[0] - a[0]) * (b[1] - a[1]) - (c[1] - a[1]) * (b[0] - a[0])

    const area = edge(p0, p1, p2)
    if (Math.abs(area) < 1e-6) return
    const inv = 1 / area

    for (let y = minY; y <= maxY; y++) {
      for (let x = minX; x <= maxX; x++) {
        const w0 = edge(p1, p2, [x, y, 0]) * inv
        const w1 = edge(p2, p0, [x, y, 0]) * inv
        const w2 = edge(p0, p1, [x, y, 0]) * inv
        if (w0 < 0 || w1 < 0 || w2 < 0) continue

        const z = z0 * w0 + z1 * w1 + z2 * w2
        if (z > zbuf[y][x]) {
          const nx = n0[0] * w0 + n1[0] * w1 + n2[0] * w2
          const ny = n0[1] * w0 + n1[1] * w1 + n2[1] * w2
          const nz = n0[2] * w0 + n1[2] * w1 + n2[2] * w2
          const nlen = Math.hypot(nx, ny, nz)
          if (nlen < 1e-6) continue
          zbuf[y][x] = z
          buf[y][x] = shadeChar(nx / nlen, ny / nlen, nz / nlen, z)
        }
      }
    }
  }

  function render(ax: number, ay: number): string[] {
    // Reset buffers.
    for (let y = 0; y < height; y++) {
      for (let x = 0; x < width; x++) {
        buf[y][x] = ' '
        zbuf[y][x] = -1e9
      }
    }

    const rotated = CUBE_VERTICES.map((v) => rotate(v, ax, ay))
    const projected = rotated.map((v) => project(v, width, height))

    interface FaceInfo {
      face: Face
      vns: ReadonlyArray<Vec3>
      avgZ: number
    }
    const faceInfo: FaceInfo[] = []
    for (const face of CUBE_FACES) {
      const [nx, ny, nz] = faceNormal(face, rotated)
      const nlen = Math.hypot(nx, ny, nz)
      if (nlen === 0) continue
      const nnz = nz / nlen
      if (nnz >= 0) continue // Back-facing.
      const avgZ =
        (rotated[face[0]][2] +
          rotated[face[1]][2] +
          rotated[face[2]][2] +
          rotated[face[3]][2]) /
        4
      const vns: Vec3[] = [
        vertexNormal(face[0], rotated),
        vertexNormal(face[1], rotated),
        vertexNormal(face[2], rotated),
        vertexNormal(face[3], rotated),
      ]
      faceInfo.push({ face, vns, avgZ })
    }

    // Painter's algorithm: sort back-to-front (smaller Z = closer, draw last).
    faceInfo.sort((a, b) => b.avgZ - a.avgZ)

    for (const { face, vns } of faceInfo) {
      const p: Vec3[] = [
        projected[face[0]],
        projected[face[1]],
        projected[face[2]],
        projected[face[3]],
      ]
      drawTriangle(p[0], p[1], p[2], vns[0], vns[1], vns[2])
      drawTriangle(p[0], p[2], p[3], vns[0], vns[2], vns[3])
    }

    return buf.map((row) => row.join(''))
  }

  return { width, height, resize, render }
}
