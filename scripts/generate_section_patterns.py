"""
Generates the four section-accent SVGs used on the actual site (one per
section: Projects, Blog, Notes & Finds, Photos), reusing generate_halftone
and generate_topographic from generate_patterns.py with each section's
accent color and a different pattern/density/seed for variety.

Run with:  python generate_section_patterns.py
Writes into ../assets/patterns/
"""
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from generate_patterns import generate_halftone, generate_topographic

OUT_DIR = os.path.join(os.path.dirname(__file__), "..", "assets", "patterns")
os.makedirs(OUT_DIR, exist_ok=True)

def out(name):
    return os.path.join(OUT_DIR, name)

# Generated at the actual display size (900x360, a wide top banner) instead
# of a small patch stretched by CSS, so the lines/dots stay crisp.
# resolution=2 on the topo ones keeps compute time reasonable at this size,
# it doesn't cost visible smoothness since these are vector paths anyway.

# Projects & CV -- topographic, rust, new seed
generate_topographic(dict(
    width_px=900, height_px=360,
    seed=205, freq=0.016, warp=0.4, n_levels=42, resolution=2, smoothing=50,
    color="#A9633B", line_width=1.2,
    out_file=out("projects.svg"),
))

# Blog -- halftone, indigo, sparser
generate_halftone(dict(
    width_px=900, height_px=360,
    spacing=13, dot_radius=1.4,
    color="#2F3E63",
    out_file=out("blog.svg"),
))

# Notes & Finds -- topographic, sage, new seed
generate_topographic(dict(
    width_px=900, height_px=360,
    seed=88, freq=0.016, warp=0.4, n_levels=24, resolution=2, smoothing=50,
    color="#5E7350", line_width=1.1,
    out_file=out("notes.svg"),
))

# Photos -- halftone, gold
generate_halftone(dict(
    width_px=900, height_px=360,
    spacing=15, dot_radius=1.1,
    color="#B8863B",
    out_file=out("photos.svg"),
))

print("done")
