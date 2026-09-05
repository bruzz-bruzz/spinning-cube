/**
 * Spinning Donut — TypeScript port of Andy Sloane's classic donut.c
 * (2006). Renders a 3D torus in ASCII using the same shading pipeline
 * as the cube renderer (z-buffer, per-pixel lighting, SHADE_CHARS ramp).
 *
 * The torus is generated as a ring of points (angle A) swept around a
 * circular cross-section (angle B). For each surface point the normal
 * is computed analytically from the parameters, which is exact and
 * much faster than the cube's Gouraud interpolation.
 *
 * Public API mirrors the cube renderer:
 *   const state = createDonutRenderer()
 *   state.resize(width, height)
 *   const rows = state.render(ax, ay)
 */

const SHADE_CHARS = " .'`,:;-+=*#%@$"

/** Key light direction. Matches the cube renderer. */
const LIGHT: [number, number, number] = (() => {
  const v: [number, number, number] = [-0.5, 0.5, -1.0]
  const len = Math.hypot(v[0], v[1], v[2])
  return [v[0] / len, v[1] / len, v[2] / len]
})()

/** Major radius (distance from center of torus to center of tube). */
const R = 1.0
/** Minor radius (tube thickness). */
const r = 0.4

/**
 * Number of subdivisions along the two angles of the torus.
 * More = smoother, but slower. 90x24 gives a nice donut on a typical
 * terminal-sized buffer.
 */
const A_STEPS = 90
const B_STEPS = 24

export interface DonutRendererState {
  width: number
  height: number
  resize(width: number, height: number): void
  render(ax: number, ay: number): string[]
}

export function createDonutRenderer(
  initialWidth = 80,
  initialHeight = 24,
): DonutRendererState {
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
   * Map a normalised normal + depth to a shade character. Same recipe
   * as the cube (key + fill + specular) so the two renderers feel
   * consistent.
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

  /**
   * Pick a projection scale that fits the donut in the current
   * character buffer. Mirrors donut.c: screen_x = x * (K / z) where
   * K is the scale. We pick K so the donut's outer diameter occupies
   * about 80% of the smaller buffer dimension.
   */
  function computeScale(): { k: number; aspect: number } {
    const aspect = 0.5 // Compensate for tall terminal chars.
    const distance = 4
    // Effective perspective factor is 1 / (z + distance). At z=0
    // (the front of the donut) invZ = 1/distance. We want the
    // screen radius to be about 40% of the buffer in each dim, so:
    //   screenRadius = (R + r) * invZ * k
    //   k = screenRadius / ((R + r) * invZ)
    // Use a small margin (0.4) to leave breathing room.
    const worldR = R + r
    const maxScreenX = width * 0.45
    const maxScreenY = height * 2 * 0.45
    const targetRadius = Math.min(maxScreenX, maxScreenY)
    const k = (targetRadius * distance) / worldR
    return { k, aspect }
  }

  function render(ax: number, ay: number): string[] {
    // Reset buffers.
    for (let y = 0; y < height; y++) {
      for (let x = 0; x < width; x++) {
        buf[y][x] = ' '
        zbuf[y][x] = -1e9
      }
    }

    const cx = Math.cos(ax)
    const sx = Math.sin(ax)
    const cy = Math.cos(ay)
    const sy = Math.sin(ay)

    const { k, aspect } = computeScale()
    const distance = 4

    // Single-pass z-buffer rendering. For each torus surface point we
    // compute its projected screen position and compare 1/z to the
    // buffer; only the front-most point per pixel wins.

    for (let i = 0; i < A_STEPS; i++) {
      const A = (i / A_STEPS) * Math.PI * 2
      const cosA = Math.cos(A)
      const sinA = Math.sin(A)
      for (let j = 0; j < B_STEPS; j++) {
        const B = (j / B_STEPS) * Math.PI * 2
        const cosB = Math.cos(B)
        const sinB = Math.sin(B)

        // Point on the torus surface, before any rotation.
        const px0 = (R + r * cosA) * cosB
        const py0 = (R + r * cosA) * sinB
        const pz0 = r * sinA

        // Rotate around X (tilt), then Y (spin). Matches the cube.
        const y1 = py0 * cx - pz0 * sx
        const z1 = py0 * sx + pz0 * cx
        const x1 = px0 * cy + z1 * sy
        const z2 = -px0 * sy + z1 * cy

        // Analytic normal of the torus in the un-rotated frame.
        const nx0 = cosA * cosB
        const ny0 = cosA * sinB
        const nz0 = sinA
        // Rotate normal by the same matrix as the position.
        const ny1 = ny0 * cx - nz0 * sx
        const nz1 = ny0 * sx + nz0 * cx
        const nx1 = nx0 * cy + nz1 * sy
        const nz2 = -nx0 * sy + nz1 * cy

        // Skip back-facing points.
        if (nz2 > 0) continue

        // Perspective project.
        const z = z2 + distance
        const invZ = 1 / z
        const sxPix = Math.round(width / 2 + x1 * invZ * k)
        const syPix = Math.round(height / 2 - y1 * invZ * k * aspect)
        if (sxPix < 0 || sxPix >= width || syPix < 0 || syPix >= height) {
          continue
        }

        if (invZ > zbuf[syPix][sxPix]) {
          zbuf[syPix][sxPix] = invZ
          buf[syPix][sxPix] = shadeChar(nx1, ny1, nz2, z)
        }
      }
    }

    return buf.map((row) => row.join(''))
  }

  return { width, height, resize, render }
}
