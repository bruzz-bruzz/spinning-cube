"""
Spinning Cube in the Terminal
=============================
A classic 3D surface cube rendered in ASCII that spins in the terminal.

Inspired by Andy Sloane's donut.c, this rotates an 8-vertex cube, projects
it to 2D with simple perspective, applies Lambertian shading, and fills the
faces with ASCII characters based on brightness.

Run interactively to see it animate. Ctrl+C to exit.
"""

import math
import sys
import time

# Try curses first (smooth full-screen on Linux/macOS).
# Fall back to plain ANSI-stdout when curses is unavailable (e.g. Windows).
try:
    import curses
    _USE_CURSES = True
except Exception:
    _USE_CURSES = False


# --------------------------------------------------------------------------- #
# Geometry
# --------------------------------------------------------------------------- #

# Cube vertices (size 2, centered at origin)
CUBE_VERTICES = [
    (-1, -1, -1),  # 0
    ( 1, -1, -1),  # 1
    ( 1,  1, -1),  # 2
    (-1,  1, -1),  # 3
    (-1, -1,  1),  # 4
    ( 1, -1,  1),  # 5
    ( 1,  1,  1),  # 6
    (-1,  1,  1),  # 7
]

# Six faces (CCW winding when viewed from outside).
CUBE_FACES = [
    (0, 3, 2, 1),  # -Z front
    (5, 6, 7, 4),  # +Z back
    (3, 7, 6, 2),  # +Y top
    (4, 0, 1, 5),  # -Y bottom
    (1, 2, 6, 5),  # +X right
    (4, 7, 3, 0),  # -X left
]

# Brightness ramp: dim -> bright. More characters = smoother gradient.
# The end of the ramp has dense, "heavy" characters (%, #, @, $) that
# read as bright even at small font sizes, while the start is sparse
# (space, period, comma, apostrophe) for subtle dark areas.
SHADE_CHARS = " .'`,:;-+=*#%@$"


# --------------------------------------------------------------------------- #
# Math helpers
# --------------------------------------------------------------------------- #

def rotate(point, ax, ay):
    """Rotate a 3D point around X then Y by angles ``ax`` and ``ay`` (radians)."""
    x, y, z = point
    # Rotation around X (tilt)
    cy = math.cos(ax)
    sy = math.sin(ax)
    y, z = y * cy - z * sy, y * sy + z * cy
    # Rotation around Y (spin)
    cx = math.cos(ay)
    sx = math.sin(ay)
    x, z = x * cx + z * sx, -x * sx + z * cx
    return x, y, z


def project(point, width, height, distance=4, cube_size=2.0):
    """Project a 3D point to 2D screen coordinates with simple perspective.

    Terminal characters are roughly twice as tall as they are wide, so
    the vertical axis is scaled by 0.5 to make the cube look like a
    cube rather than a stretched pillar.
    """
    x, y, z = point
    z += distance
    # Perspective: scale by 1/z so farther points are smaller.
    factor = 1.0 / z
    # Scale so the cube fills the screen with a small margin.
    k = cube_size * min(width, height * 2) * 0.55
    sx = int(width / 2 + x * factor * k)
    # Halve the Y scale so the cube isn't vertically squished.
    sy = int(height / 2 - y * factor * k * 0.5)
    return sx, sy, z


def face_normal(face, vertices):
    """Compute the (un-normalized) outward normal of a planar face."""
    v0 = vertices[face[0]]
    v1 = vertices[face[1]]
    v2 = vertices[face[2]]
    ex, ey, ez = (v1[0] - v0[0], v1[1] - v0[1], v1[2] - v0[2])
    fx, fy, fz = (v2[0] - v0[0], v2[1] - v0[1], v2[2] - v0[2])
    nx = ey * fz - ez * fy
    ny = ez * fx - ex * fz
    nz = ex * fy - ey * fx
    return nx, ny, nz


def vertex_normal(vertex_idx, faces, vertices):
    """Average the normals of the faces that share ``vertex_idx``.

    For a cube, every vertex is shared by exactly 3 faces, so the average
    is the unweighted sum divided by 3. This gives a smooth gradient
    across each face (Gouraud-style shading) instead of one flat shade.
    """
    nx = ny = nz = 0.0
    for face in faces:
        if vertex_idx in face:
            fnx, fny, fnz = face_normal(face, vertices)
            nx += fnx
            ny += fny
            nz += fnz
    return nx, ny, nz


# --------------------------------------------------------------------------- #
# Rendering
# --------------------------------------------------------------------------- #

def render(width, height, ax, ay):
    """Render one frame of the cube. Returns a list of strings (one per row)."""
    # Transform vertices
    rotated = [rotate(v, ax, ay) for v in CUBE_VERTICES]

    # Transform + project vertices
    projected = [project(v, width, height) for v in rotated]

    # Light direction (normalized) - comes from upper-right-front
    light = (0.5, 0.5, -1.0)
    l_len = math.sqrt(sum(c * c for c in light))
    light = tuple(c / l_len for c in light)

    # Compute face brightness (Lambertian-ish) and only keep front-facing ones.
    # Also collect per-vertex normals for smooth shading within the face.
    face_info = []
    for face in CUBE_FACES:
        nx, ny, nz = face_normal(face, rotated)
        n_len = math.sqrt(nx * nx + ny * ny + nz * nz)
        if n_len == 0:
            continue
        nx, ny, nz = nx / n_len, ny / n_len, nz / n_len
        # Camera sits at +Z, so faces with negative Z normal point toward viewer.
        if nz >= 0:
            continue
        # Per-vertex normals (averaged from the 3 adjacent face normals).
        vns = [vertex_normal(i, CUBE_FACES, rotated) for i in face]
        face_info.append((face, vns))

    # Sort back-to-front by average z so closer faces overwrite farther ones.
    def avg_z(face):
        zs = [projected[i][2] for i in face]
        return sum(zs) / len(zs)

    face_info.sort(key=lambda fi: -avg_z(fi[0]))

    # Initialize buffer + z-buffer
    buf = [[" " for _ in range(width)] for _ in range(height)]
    zbuf = [[-1e9 for _ in range(width)] for _ in range(height)]

    def shade_char(nx, ny, nz, z):
        """Map a (normalized) normal and depth to a shade character.

        Uses a key light from the upper-right-front plus a softer fill
        light from the lower-left so the dark side of the cube still has
        visible detail instead of going pitch black. Also adds a small
        specular highlight where the surface faces the key light directly.
        """
        # Key light: strong, comes from upper-right-front.
        key_dot = nx * light[0] + ny * light[1] + nz * light[2]
        key = max(0.0, key_dot)
        # Fill light: weaker, from the opposite side.
        fill = max(0.0, -nx * 0.4 + -ny * 0.4 + -nz * 0.2)
        # Specular highlight: small bright spot where the surface faces
        # the light most directly. This makes the cube look "shiny".
        specular = key_dot ** 8 if key_dot > 0 else 0
        # Distance falloff: pixels farther from the camera are slightly dimmer.
        depth_factor = 1.0 - max(0.0, min(0.15, (z - 3) * 0.04))
        # Ambient floor + key + fill + specular.
        b = (0.16 + 0.62 * key + 0.15 * fill + 0.18 * specular) * depth_factor
        idx = min(len(SHADE_CHARS) - 1, max(0, int(b * len(SHADE_CHARS))))
        return SHADE_CHARS[idx]

    # Rasterize a triangle with per-pixel shading (Gouraud-style).
    def draw_triangle(p0, p1, p2, n0, n1, n2):
        (x0, y0, z0), (x1, y1, z1), (x2, y2, z2) = p0, p1, p2
        min_x = max(0, min(x0, x1, x2))
        max_x = min(width - 1, max(x0, x1, x2))
        min_y = max(0, min(y0, y1, y2))
        max_y = min(height - 1, max(y0, y1, y2))

        def edge(a, b, c):
            ax_, ay_, _ = a
            bx_, by_, _ = b
            cx_, cy_, _ = c
            return (cx_ - ax_) * (by_ - ay_) - (cy_ - ay_) * (bx_ - ax_)

        area = edge(p0, p1, p2)
        if abs(area) < 1e-6:
            return
        inv = 1.0 / area

        for y in range(min_y, max_y + 1):
            for x in range(min_x, max_x + 1):
                p = (x, y, 0)
                w0 = edge(p1, p2, p) * inv
                w1 = edge(p2, p0, p) * inv
                w2 = edge(p0, p1, p) * inv
                if w0 < 0 or w1 < 0 or w2 < 0:
                    continue
                z = z0 * w0 + z1 * w1 + z2 * w2
                if z > zbuf[y][x]:
                    # Interpolate normal, renormalise, then shade.
                    nx = n0[0] * w0 + n1[0] * w1 + n2[0] * w2
                    ny = n0[1] * w0 + n1[1] * w1 + n2[1] * w2
                    nz = n0[2] * w0 + n1[2] * w1 + n2[2] * w2
                    nlen = math.sqrt(nx * nx + ny * ny + nz * nz)
                    if nlen < 1e-6:
                        continue
                    zbuf[y][x] = z
                    buf[y][x] = shade_char(nx / nlen, ny / nlen, nz / nlen, z)

    for face, vns in face_info:
        p = [projected[i] for i in face]
        # Split quad into two triangles
        draw_triangle(p[0], p[1], p[2], vns[0], vns[1], vns[2])
        draw_triangle(p[0], p[2], p[3], vns[0], vns[2], vns[3])

    return ["".join(row) for row in buf]


# --------------------------------------------------------------------------- #
# Main loop
# --------------------------------------------------------------------------- #

def run_curses(stdscr):
    curses.curs_set(0)
    stdscr.nodelay(True)
    height, width = stdscr.getmaxyx()
    height = min(height, 60)
    width = min(width, 120)

    ax = math.radians(20)
    ay = 0.0
    last = time.time()

    while True:
        try:
            key = stdscr.getch()
        except Exception:
            key = -1
        if key in (27, ord("q")):  # ESC or q
            return

        stdscr.erase()
        rows = render(width, height, ax, ay)
        try:
            for i, row in enumerate(rows):
                if i >= height:
                    break
                stdscr.addstr(i, 0, row[:width])
        except curses.error:
            pass  # Window too small for this frame
        stdscr.refresh()

        now = time.time()
        dt = now - last
        last = now
        ay += 1.2 * dt
        ax += 0.6 * dt

        time.sleep(max(0.0, 1 / 30 - dt))


def run_plain(width=80, height=24):
    """Plain-stdout fallback. Uses ANSI escapes so output looks right when piped."""
    ax = math.radians(20)
    ay = 0.0
    try:
        while True:
            sys.stdout.write("\x1b[2J\x1b[H")
            rows = render(width, height, ax, ay)
            sys.stdout.write("\n".join(rows) + "\n")
            sys.stdout.flush()
            ay += 0.08
            ax += 0.04
            time.sleep(0.05)
    except KeyboardInterrupt:
        return


def parse_args():
    import argparse
    p = argparse.ArgumentParser(
        description="Render a spinning 3D cube in the terminal using ASCII art.",
    )
    p.add_argument("--width", type=int, default=None,
                   help="Override terminal width (plain mode).")
    p.add_argument("--height", type=int, default=None,
                   help="Override terminal height (plain mode).")
    p.add_argument("--once", action="store_true",
                   help="Render a single frame and exit (useful for tests).")
    p.add_argument("--spins", type=float, default=None,
                   help="With --once, rotate this many full turns around Y.")
    return p.parse_args()


def main():
    args = parse_args()

    if args.once:
        # Render a single static frame and exit. Handy for piping to a file
        # or capturing an image in a test.
        import math
        width = args.width or 80
        height = args.height or 24
        ay = (args.spins or 0.3) * 2 * math.pi
        ax = math.radians(20)
        rows = render(width, height, ax, ay)
        sys.stdout.write("\n".join(rows) + "\n")
        return

    if _USE_CURSES and sys.stdout.isatty():
        try:
            curses.wrapper(run_curses)
        except KeyboardInterrupt:
            pass
    else:
        try:
            width = args.width or 80
            height = args.height or 24
            run_plain(width=width, height=height)
        except KeyboardInterrupt:
            pass


if __name__ == "__main__":
    main()
