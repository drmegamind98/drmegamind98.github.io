"""
Generates the three decorative SVG patterns for the Field Notes site:
halftone, topographic contours, and guilloche.

Run with:  python generate_patterns.py
Produces:  halftone.svg, topographic.svg, guilloche.svg (in this folder)

Edit the CONFIG dict for whichever pattern you want to change, then re-run.
Each config's comments explain what that parameter controls.
"""
import numpy as np
import matplotlib
matplotlib.use("SVG")
import matplotlib.pyplot as plt
from opensimplex import OpenSimplex
from scipy.ndimage import gaussian_filter


# ============================================================
# HALFTONE  (grid of dots)
# ============================================================
HALFTONE_CONFIG = dict(
    width_px=480,
    height_px=380,
    spacing=10,        # distance between dots, in px. Smaller number = denser grid.
    dot_radius=1.6,   # radius of each dot, in px.
    color="#A9633B",  # any hex color
    out_file="halftone.svg",
)

def generate_halftone(cfg):
    w, h = cfg["width_px"], cfg["height_px"]
    fig = plt.figure(figsize=(w / 100, h / 100), dpi=100)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, w)
    ax.set_ylim(0, h)
    ax.axis("off")
    ax.set_aspect("equal")

    xs = np.arange(0, w, cfg["spacing"])
    ys = np.arange(0, h, cfg["spacing"])
    X, Y = np.meshgrid(xs, ys)
    ax.scatter(X.ravel(), Y.ravel(), s=(cfg["dot_radius"] * 2) ** 2, c=cfg["color"], linewidths=0)

    fig.savefig(cfg["out_file"], transparent=True)
    print("wrote", cfg["out_file"])


# ============================================================
# TOPOGRAPHIC  (Simplex noise + domain warp + contour tracing)
# ============================================================
TOPO_CONFIG = dict(
    width_px=480,
    height_px=380,
    seed=6969,          # change for a different random layout, same style
    freq=0.016,       # base noise frequency. Smaller = larger, calmer shapes.
    warp=0.4,         # domain-warp strength. 0 = plain rounded contours, higher = more swirl/flow.
    n_levels=30,       # number of contour lines. Fewer = sparser/calmer, more = denser.
    resolution=1,     # px per sample. Lower = smoother curves but slower to compute.
    smoothing=50,    # gaussian blur applied to the noise field before contouring. Higher = smoother/rounder lines, 0 = off.
    color="#A9633B",
    line_width=1.2,
    out_file="topographic.svg",
)

def generate_topographic(cfg):
    simplex = OpenSimplex(seed=cfg["seed"])

    def noise2(x, y):
        return simplex.noise2(x, y)

    def fbm(x, y, octaves=4, lac=2.0, gain=0.5):
        amp, freq, total = 0.5, 1.0, 0.0
        for _ in range(octaves):
            total += amp * noise2(x * freq, y * freq)
            freq *= lac
            amp *= gain
        return total

    def warped(x, y, warp):
        qx = fbm(x, y)
        qy = fbm(x + 5.2, y + 1.3)
        rx = fbm(x + warp * qx + 1.7, y + warp * qy + 9.2)
        ry = fbm(x + warp * qx + 8.3, y + warp * qy + 2.8)
        return fbm(x + warp * rx, y + warp * ry)

    w, h, res, freq = cfg["width_px"], cfg["height_px"], cfg["resolution"], cfg["freq"]
    xs = np.arange(0, w, res) * freq
    ys = np.arange(0, h, res) * freq
    X, Y = np.meshgrid(xs, ys)
    Z = np.vectorize(warped)(X, Y, cfg["warp"])
    if cfg.get("smoothing", 0) > 0:
        Z = gaussian_filter(Z, sigma=cfg["smoothing"])


    fig = plt.figure(figsize=(w / 100, h / 100), dpi=100)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, X.shape[1] - 1)
    ax.set_ylim(0, X.shape[0] - 1)
    ax.axis("off")

    levels = np.linspace(Z.min(), Z.max(), cfg["n_levels"])
    ax.contour(Z, levels=levels, colors=cfg["color"], linewidths=cfg["line_width"])

    fig.savefig(cfg["out_file"], transparent=True)
    print("wrote", cfg["out_file"])


# ============================================================
# GUILLOCHE  (overlapping hypotrochoid / spirograph rosettes)
# ============================================================
GUILLOCHE_CONFIG = dict(
    width_px=480,
    height_px=380,
    R=150,            # outer radius of the base rosette, in px
    r=57,              # radius of the "rolling circle". Non-round ratios of R/r give more complex weaves.
    d=58,              # pen offset from the rolling circle's center. Controls how "loopy" each curve is.
    num_curves=3,      # how many rotated copies are overlaid to build the woven look
    rotation_step=10,   # degrees between each overlaid copy
    n_points=3000,     # curve resolution. Higher = smoother lines, slower to draw.
    color="#A9633B",
    line_width=0.7,
    out_file="guilloche.svg",
)

def generate_guilloche(cfg):
    w, h = cfg["width_px"], cfg["height_px"]
    cx, cy = w / 2, h / 2
    R, r, d = cfg["R"], cfg["r"], cfg["d"]

    t = np.linspace(0, 2 * np.pi * 20, cfg["n_points"])

    fig = plt.figure(figsize=(w / 100, h / 100), dpi=100)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, w)
    ax.set_ylim(0, h)
    ax.axis("off")
    ax.set_aspect("equal")

    for i in range(cfg["num_curves"]):
        phase = np.radians(i * cfg["rotation_step"])
        x = (R - r) * np.cos(t + phase) + d * np.cos((R - r) / r * t)
        y = (R - r) * np.sin(t + phase) - d * np.sin((R - r) / r * t)
        ax.plot(cx + x, cy + y, color=cfg["color"], linewidth=cfg["line_width"])

    fig.savefig(cfg["out_file"], transparent=True)
    print("wrote", cfg["out_file"])


if __name__ == "__main__":
    generate_halftone(HALFTONE_CONFIG)
    generate_topographic(TOPO_CONFIG)
    generate_guilloche(GUILLOCHE_CONFIG)
