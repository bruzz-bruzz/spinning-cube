"""
Spinning Donut in the Terminal
=============================
A 3D ASCII torus that spins in the terminal. Sister script to ``cube.py``:
same shading pipeline, same brightness ramp, same curses/ANSI double
runtime, but the geometry is a parametric torus instead of a unit cube.

The renderer follows Andy Sloane's classic donut.c algorithm (2006):
sample a ring of points on the surface of a torus, rotate them every
frame, perspective-project them, and use a z-buffer so the front of the
torus correctly occludes the back. The normal at each surface point is
computed analytically (no per-vertex averaging needed) which is exact
and fast.

Run interactively to see it animate. Ctrl+C to exit, 'q' or ESC also
quits under curses.
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

# Major (ring) and minor (tube) radii of the torus.
R = 1.0
r = 0.4

# Angular subdivisions of the torus. More = smoother but slower. 90 x 24
# gives a clean donut at typical terminal sizes.
A_STEPS = 90
B_STEPS = 24

# Brightness ramp: dim -> bright. Matches cube.py exactly so the two
# scenes feel like they belong together.
SHADE_CHARS = " .'`,:;-+=*#%@$"


# --------------------------------------------------------------------------- #
# Math helpers
# --------------------------------------------------------------------------- #

def rotate(point, ax, ay):
    """Rotate a 3D point around X then Y by angles ``ax`` and ``ay`` (radians).

    Identical to cube.py's rotate() so the two renderers animate the same
    way when both are running.
    """
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


# --------------------------------------------------------------------------- #
# Rendering
# --------------------------------------------------------------------------- #

def render(width, height, ax, ay):
    """Render one frame of the donut. Returns a list of strings (one per row).

    The torus is generated as a ring of points (angle B) swept around a
    circular cross-section (angle A). For each surface point we compute
    the analytic outward normal in the un-rotated frame, rotate both the
    position and the normal by the same matrix, project to 2D, and write
    a shade character if the point is closer than what's already in the
    z-buffer.
    """
    # Pre-compute rotation coefficients.
    cax = math.cos(ax)
    sax = math.sin(ax)
    cay = math.cos(ay)
    say = math.sin(ay)

    # Light direction (upper-right-front) — matches cube.py.
    light = (0.5, 0.5, -1.0)
    l_len = math.sqrt(sum(c * c for c in light))
    light = tuple(c / l_len for c in light)

    # Pick a projection scale so the donut's outer diameter fills
    # ~90% of the smaller buffer dimension.
    distance = 4.0
    world_r = R + r
    max_screen_x = width * 0.45
    max_screen_y = height * 2 * 0.45  # account for tall terminal chars
    target_radius = min(max_screen_x, max_screen_y)
    k = (target_radius * distance) / world_r
    aspect = 0.5  # Compensate for tall terminal characters.

    # Initialize buffer + z-buffer.
    buf = [[" " for _ in range(width)] for _ in range(height)]
    zbuf = [[-1e9 for _ in range(width)] for _ in range(height)]

    def shade_char(nx, ny, nz, z):
        """Map a (normalized) normal and depth to a shade character.

        Same recipe as the cube: key + fill + specular + depth falloff.
        """
        key_dot = nx * light[0] + ny * light[1] + nz * light[2]
        key = max(0.0, key_dot)
        fill = max(0.0, -nx * 0.4 + -ny * 0.4 + -nz * 0.2)
        specular = key_dot ** 8 if key_dot > 0 else 0
        depth_factor = 1.0 - max(0.0, min(0.15, (z - 3) * 0.04))
        b = (0.16 + 0.62 * key + 0.15 * fill + 0.18 * specular) * depth_factor
        idx = min(len(SHADE_CHARS) - 1, max(0, int(b * len(SHADE_CHARS))))
        return SHADE_CHARS[idx]

    # Pre-compute the sin/cos tables for the two angles. Not strictly
    # necessary at these step counts, but it keeps the inner loop tight.
    for i in range(A_STEPS):
        A = (i / A_STEPS) * math.tau  # 2*pi
        cosA = math.cos(A)
        sinA = math.sin(A)
        for j in range(B_STEPS):
            B = (j / B_STEPS) * math.tau
            cosB = math.cos(B)
            sinB = math.sin(B)

            # Point on the torus surface, before any rotation. The tube
            # cross-section lies in the local XZ plane, offset from the
            # world origin by R along the world X axis to form the ring.
            px0 = (R + r * cosA) * cosB
            py0 = (R + r * cosA) * sinB
            pz0 = r * sinA

            # Rotate around X (tilt), then Y (spin) — same order as cube.
            y1 = py0 * cax - pz0 * sax
            z1 = py0 * sax + pz0 * cax
            x1 = px0 * cay + z1 * say
            z2 = -px0 * say + z1 * cay

            # Analytic normal of the torus in the un-rotated frame.
            nx0 = cosA * cosB
            ny0 = cosA * sinB
            nz0 = sinA
            # Rotate normal by the same matrix as the position.
            ny1 = ny0 * cax - nz0 * sax
            nz1 = ny0 * sax + nz0 * cax
            nx1 = nx0 * cay + nz1 * say
            nz2 = -nx0 * say + nz1 * cay

            # Skip back-facing points.
            if nz2 > 0:
                continue

            # Perspective project.
            z = z2 + distance
            inv_z = 1.0 / z
            sx = int(width / 2 + x1 * inv_z * k)
            sy = int(height / 2 - y1 * inv_z * k * aspect)
            if sx < 0 or sx >= width or sy < 0 or sy >= height:
                continue

            if inv_z > zbuf[sy][sx]:
                zbuf[sy][sx] = inv_z
                buf[sy][sx] = shade_char(nx1, ny1, nz2, z)

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
        description="Render a spinning 3D donut in the terminal using ASCII art.",
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
        width = args.width or 80
        height = args.height or 24
        ay = (args.spins or 0.3) * math.tau
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
