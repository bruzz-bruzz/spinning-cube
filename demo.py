"""Render a few static demo frames of the spinning scenes.

Run with ``python demo.py``. Saves ASCII art to ``demo_*.txt``.
Useful for showing what the animation looks like without launching it.
"""

import os

import cube
import donut


def save_frame(renderer, ax, ay, width, height, path):
    rows = renderer.render(width, height, ax, ay)
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(rows) + "\n")
    print(f"Wrote {path}")


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    width, height = 64, 22
    # Four nicely rotated angles showing the cube from different sides.
    cube_frames = [
        ("demo_front.txt",  0.30, 0.00),
        ("demo_angle.txt",  0.45, 0.40),
        ("demo_side.txt",   0.20, 1.55),
        ("demo_top.txt",    1.30, 0.50),
    ]
    for name, ax, ay in cube_frames:
        save_frame(cube, ax, ay, width, height, os.path.join(here, name))

    # One well-posed donut frame to show the torus off.
    save_frame(donut, 0.40, 0.60, width, height,
               os.path.join(here, "demo_donut.txt"))


if __name__ == "__main__":
    main()
