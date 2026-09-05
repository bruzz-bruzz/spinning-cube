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

# Brightness ramp: dim -> bright with more characters for smoother gradients
SHADE_CHARS = " .,:;-+=!*#%@"

# ANSI true-colour (24-bit) per face. Each face gets a distinct base colour
# and the SHADE_CHARS pick the brightness within that colour. Disable
# globally by setting ``USE_COLOR = False`` below.
USE_COLOR = True

# (R, G, B) in 0-255. One colour per face in the order of CUBE_FACES.
FACE_COLORS = [
    (255,  90,  90),   # -Z front    (warm red)
    ( 90,  90, 255),   # +Z back     (blue)
    (255, 230,  90),   # +Y top      (yellow)
    (130,  90, 255),   # -Y bottom   (purple)
    ( 90, 230,  90),   # +X right    (green)
    (255, 150,  90),   # -X left     (orange)
]


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


def project(point, width, height, distance=5):
    """Project a 3D point to 2D screen coordinates with perspective.

    Terminal characters are roughly 2x taller than they are wide, so the
    effective square budget is ``min(width, height*2)``. This keeps the
    cube looking like a cube (not a tall pillar) on a standard terminal.
    """
    x, y, z = point
    z += distance
    if z <= 0.01:
        return -10000.0, -10000.0, 1e9
    factor = 1.0 / z
    # Scale: cube (side ~2) should fill ~most of the shorter screen dim.
    # Aspect-compensated for tall terminal characters. 0.65 leaves a
    # comfortable margin so the cube fits even at a 25deg X tilt.
    k = 0.65 * min(width, height * 2)
    sx = width / 2 + x * factor * k
    # Shift slightly upward so the cube is vertically centred in the
    # visible character rows (compensates for X-tilt bias).
    sy = height / 2 - y * factor * k + 0.5
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


# --------------------------------------------------------------------------- #
# Rendering
# --------------------------------------------------------------------------- #

def render(width, height, ax, ay):
    """Render one frame of the cube. Returns a list of strings (one per row)."""
    # Transform vertices
    rotated = [rotate(v, ax, ay) for v in CUBE_VERTICES]

    # Transform + project vertices
    projected = [project(v, width, height) for v in rotated]

    # Light direction (normalized) - upper-right-front, more directional
    # so the contrast between faces is more dramatic.
    light = (0.6, 0.8, -0.2)
    l_len = math.sqrt(sum(c * c for c in light))
    light = tuple(c / l_len for c in light)

    # Compute per-vertex normals (averaged from the 3 adjacent face normals).
    # These are used for smooth per-pixel shading across each face.
    def vertex_normal(vi):
        # Find the 3 faces that include this vertex.
        adj = [face_normal(f, rotated) for f in CUBE_FACES if vi in f]
        if not adj:
            return (0.0, 0.0, 0.0)
        nx = sum(n[0] for n in adj)
        ny = sum(n[1] for n in adj)
        nz = sum(n[2] for n in adj)
        nl = math.sqrt(nx * nx + ny * ny + nz * nz)
        if nl == 0:
            return (0.0, 0.0, 0.0)
        return (nx / nl, ny / nl, nz / nl)

    # Build face info with indices for coloring
    face_info_with_idx = []
    for face_idx, face in enumerate(CUBE_FACES):
        nx, ny, nz = face_normal(face, rotated)
        n_len = math.sqrt(nx * nx + ny * ny + nz * nz)
        if n_len == 0:
            continue
        nx, ny, nz = nx / n_len, ny / n_len, nz / n_len
        # Camera sits at +Z, so faces with negative Z normal point toward viewer.
        if nz >= 0:
            continue
        # Average depth of the face for sorting back-to-front.
        z_avg = sum(rotated[i][2] for i in face) / 4.0
        # Per-vertex normals (for smooth shading within the face).
        vns = [vertex_normal(i) for i in face]
        face_info_with_idx.append((face_idx, face, z_avg, vns))

    # Sort back-to-front: faces with smaller average z (closer to camera) drawn last.
    face_info_with_idx.sort(key=lambda fi: fi[2])

    # Initialize buffer + z-buffer.
    # zbuf is "the closest z seen at this pixel so far", initialised to "far".
    buf = [[" " for _ in range(width)] for _ in range(height)]
    zbuf = [[1e9 for _ in range(width)] for _ in range(height)]

    SHADE_LEN = len(SHADE_CHARS)

    def shade_char(nx, ny, nz):
        """Return the brightness character for a given (already-normalised) normal."""
        dot = nx * light[0] + ny * light[1] + nz * light[2]
        # Ambient term: unlit faces are dim but not pitch black.
        b = 0.10 + 0.90 * max(0.0, dot)
        idx = int(b * (SHADE_LEN - 1) + 0.5)
        if idx < 0:
            idx = 0
        elif idx >= SHADE_LEN:
            idx = SHADE_LEN - 1
        return SHADE_CHARS[idx]

    def get_colored_char(char, face_idx):
        """Apply ANSI color codes to a shaded character if USE_COLOR is True."""
        if not USE_COLOR:
            return char
        
        r, g, b = FACE_COLORS[face_idx]
        # Return the character wrapped in ANSI escape code for 24-bit color
        return f"\x1b[38;2;{r};{g};{b}m{char}\x1b[0m"

    # Edge detection for silhouette enhancement - sharper outlines
    def detect_edge(x, y):
        """Check if this pixel is an edge by comparing with neighbors."""
        if x <= 0 or x >= width - 1 or y <= 0 or y >= height - 1:
            return True  # Border pixels are always edges
        
        # Get current character
        center_char = buf[y][x]
        if center_char == ' ':
            return False
        
        # Check neighboring pixels for significant changes
        neighbors = [
            buf[y-1][x-1], buf[y-1][x], buf[y-1][x+1],
            buf[y][x-1],                        buf[y][x+1],
            buf[y+1][x-1], buf[y+1][x], buf[y+1][x+1]
        ]
        
        # Edge is detected if there's a significant change in character brightness
        center_bright = SHADE_CHARS.index(center_char) if center_char in SHADE_CHARS else 0
        max_diff = 0
        
        for char in neighbors:
            if char == ' ':
                continue
            bright = SHADE_CHARS.index(char) if char in SHADE_CHARS else 0
            diff = abs(center_bright - bright)
            if diff > max_diff:
                max_diff = diff
        
        return max_diff > 2

    # Rasterize a triangle with per-pixel interpolated normal (smooth shading).
    def draw_triangle(p0, p1, p2, n0, n1, n2, face_idx):
        (x0, y0, z0), (x1, y1, z1), (x2, y2, z2) = p0, p1, p2
        # Use math.floor so negative coords round DOWN (not toward zero like int()).
        min_x = max(0, int(math.floor(min(x0, x1, x2))))
        max_x = min(width - 1, int(math.floor(max(x0, x1, x2))))
        min_y = max(0, int(math.floor(min(y0, y1, y2))))
        max_y = min(height - 1, int(math.floor(max(y0, y1, y2))))
        if min_x > max_x or min_y > max_y:
            return

        # Signed 2x area of the triangle in screen space.
        area = (x1 - x0) * (y2 - y0) - (y1 - y0) * (x2 - x0)
        if abs(area) < 0.5:
            return
        inv_area = 1.0 / area

        for y in range(min_y, max_y + 1):
            row_buf = buf[y]
            row_z = zbuf[y]
            for x in range(min_x, max_x + 1):
                # Barycentric coordinates (relative to p0).
                w1 = ((x1 - x0) * (y - y0) - (y1 - y0) * (x - x0)) * inv_area
                w2 = ((x2 - x0) * (y - y0) - (y2 - y0) * (x - x0)) * inv_area
                w0 = 1.0 - w1 - w2
                if w0 < 0 or w1 < 0 or w2 < 0:
                    continue

                # Depth test: only write if this pixel is closer than the existing one.
                z = z0 * w0 + z1 * w1 + z2 * w2
                if z >= row_z[x]:
                    continue
                row_z[x] = z

                # Interpolate normal across the face, renormalise, shade.
                nx = n0[0] * w0 + n1[0] * w1 + n2[0] * w2
                ny = n0[1] * w0 + n1[1] * w1 + n2[1] * w2
                nz = n0[2] * w0 + n1[2] * w1 + n2[2] * w2
                nl = math.sqrt(nx * nx + ny * ny + nz * nz)
                if nl < 1e-6:
                    continue
                nx, ny, nz = nx / nl, ny / nl, nz / nl
                
                # Apply edge enhancement to make silhouettes sharper
                char = shade_char(nx, ny, nz)
                if detect_edge(x, y):
                    # Edge pixels get the brightest possible character for strong outlines
                    row_buf[x] = SHADE_CHARS[-1]  # Brightest character
                else:
                    row_buf[x] = char

    for face_idx, face, _z, vns in face_info_with_idx:
        p = [projected[i] for i in face]
        # Split the quad into two triangles and rasterise each.
        # (0,1,2) and (0,2,3) - assumes faces are listed in consistent winding.
        draw_triangle(p[0], p[1], p[2], vns[0], vns[1], vns[2], face_idx)
        draw_triangle(p[0], p[2], p[3], vns[0], vns[2], vns[3], face_idx)

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
        # ``args.spins`` is None when the user didn't pass it; treat 0 as 0.
        spins = 0.3 if args.spins is None else args.spins
        ay = spins * 2 * math.pi
        ax = math.radians(25)
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
