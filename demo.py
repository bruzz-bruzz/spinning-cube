"""Render a few static demo frames of the spinning cube.

Run with ``python demo.py``. Saves ASCII art to ``demo_*.txt``.
Useful for showing what the animation looks like without launching it.
"""

import os

import cube


def save_frame(ax, ay, width, height, path):
    rows = cube.render(width, height, ax, ay)
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(rows) + "\n")
    print(f"Wrote {path}")


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    width, height = 64, 22
    # Four nicely rotated angles showing the cube from different sides.
    angles = [
        ("demo_front.txt",  0.30, 0.00),
        ("demo_angle.txt",  0.45, 0.40),
        ("demo_side.txt",   0.20, 1.55),
        ("demo_top.txt",    1.30, 0.50),
    ]
    for name, ax, ay in angles:
        save_frame(ax, ay, width, height, os.path.join(here, name))


if __name__ == "__main__":
    main()
