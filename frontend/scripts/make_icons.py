"""Generate ASCEND PWA icons (PNG) with matplotlib.

Run from the venv:  python scripts/make_icons.py
Outputs: assets/favicon.png, assets/icons/*.png
"""

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Rectangle
from pathlib import Path

ASSETS = Path(__file__).resolve().parent.parent / "assets"

BG = "#0F1115"
TEAL = "#2DD4BF"
PURPLE = "#A78BFA"


def draw_mark(size: int, rounded: bool, padding: float, out: Path) -> None:
    fig = plt.figure(figsize=(1, 1), dpi=size)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    fig.patch.set_alpha(0)
    if rounded:
        ax.add_patch(FancyBboxPatch((0, 0), 1, 1, boxstyle="round,pad=0,rounding_size=0.2",
                                    transform=ax.transAxes, facecolor=BG))
    else:
        ax.add_patch(Rectangle((0, 0), 1, 1, transform=ax.transAxes, facecolor=BG))

    # Two ascending chevrons centered on the canvas: bottom teal, top purple.
    # Vertical span 0.30-0.68 keeps the mark inside the maskable safe zone.
    bottom = [(0.34, 0.30), (0.5, 0.46), (0.66, 0.30)]
    top = [(0.34, 0.52), (0.5, 0.68), (0.66, 0.52)]
    for points, color in ((bottom, TEAL), (top, PURPLE)):
        xs, ys = zip(*points)
        ax.plot(xs, ys, color=color, linewidth=0.085, solid_capstyle="round",
                solid_joinstyle="round", antialiased=True)
    fig.savefig(out, format="png", dpi=size, transparent=True)
    plt.close(fig)
    print("wrote", out)


def main() -> None:
    icons = ASSETS / "icons"
    icons.mkdir(parents=True, exist_ok=True)
    draw_mark(64, rounded=True, padding=0.06, out=ASSETS / "favicon.png")
    draw_mark(192, rounded=True, padding=0.08, out=icons / "icon-192.png")
    draw_mark(512, rounded=True, padding=0.08, out=icons / "icon-512.png")
    draw_mark(192, rounded=False, padding=0.10, out=icons / "icon-maskable-192.png")
    draw_mark(512, rounded=False, padding=0.10, out=icons / "icon-maskable-512.png")
    draw_mark(192, rounded=True, padding=0.08, out=icons / "apple-touch-icon-192.png")
    draw_mark(192, rounded=True, padding=0.12, out=icons / "loading-animation.png")


if __name__ == "__main__":
    main()
