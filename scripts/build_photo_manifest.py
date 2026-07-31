"""
Scans photos/*.jpg (and .jpeg), reads each photo's EXIF data, writes
resized web-friendly copies, and produces photos/manifest.json for the
site's Photos section to fetch at runtime.

Run with:  python build_photo_manifest.py
Reads:     ../photos/*.jpg
Writes:    ../photos/web/<name>-thumb.jpg   (small, for the filmstrip)
           ../photos/web/<name>-full.jpg    (larger, for the lightbox)
           ../photos/manifest.json

Photos with no EXIF data still get included, just with blank fields.
Original photos in photos/ are never modified, only read.
"""
import json
import os
from fractions import Fraction

from PIL import Image, ImageOps, ExifTags

SRC_DIR = os.path.join(os.path.dirname(__file__), "..", "photos")
WEB_DIR = os.path.join(SRC_DIR, "web")
MANIFEST_PATH = os.path.join(SRC_DIR, "manifest.json")

THUMB_MAX = 500   # px, longest edge, for the filmstrip
FULL_MAX = 1800   # px, longest edge, for the lightbox
JPEG_QUALITY = 84

TAG_NAMES = {v: k for k, v in ExifTags.TAGS.items()}
GPS_TAG_NAMES = {v: k for k, v in ExifTags.GPSTAGS.items()}


def to_deg(dms, ref):
    if not dms:
        return None
    d, m, s = [float(x) for x in dms]
    deg = d + m / 60 + s / 3600
    if ref in ("S", "W"):
        deg = -deg
    return round(deg, 6)


def format_decimal(value, template="{}", max_decimals=1):
    """For values conventionally shown as decimals: aperture (f/1.4), focal length (35mm)."""
    if value is None:
        return None
    try:
        f = float(value)
    except (TypeError, ValueError):
        return None
    if f == int(f):
        return template.format(int(f))
    return template.format(round(f, max_decimals))


def format_shutter(value):
    """Shutter speed: whole/partial seconds as '2s', sub-second as a fraction like '1/250s'."""
    if value is None:
        return None
    try:
        f = float(value)
    except (TypeError, ValueError):
        return None
    if f <= 0:
        return None
    if f >= 1:
        return f"{int(f)}s" if f == int(f) else f"{round(f, 1)}s"
    frac = Fraction(f).limit_denominator(8000)
    return f"{frac.numerator}/{frac.denominator}s"


def extract_exif(img):
    exif = img.getexif()
    if not exif:
        return {}

    ifd0 = {ExifTags.TAGS.get(k, k): v for k, v in exif.items()}

    try:
        exif_ifd = exif.get_ifd(ExifTags.IFD.Exif)
        exif_ifd = {ExifTags.TAGS.get(k, k): v for k, v in exif_ifd.items()}
    except (KeyError, AttributeError):
        exif_ifd = {}

    try:
        gps_ifd = exif.get_ifd(ExifTags.IFD.GPSInfo)
        gps_ifd = {ExifTags.GPSTAGS.get(k, k): v for k, v in gps_ifd.items()}
    except (KeyError, AttributeError):
        gps_ifd = {}

    lat = to_deg(gps_ifd.get("GPSLatitude"), gps_ifd.get("GPSLatitudeRef"))
    lon = to_deg(gps_ifd.get("GPSLongitude"), gps_ifd.get("GPSLongitudeRef"))

    focal = exif_ifd.get("FocalLength")
    fnum = exif_ifd.get("FNumber")
    exposure = exif_ifd.get("ExposureTime")
    iso = exif_ifd.get("ISOSpeedRatings") or exif_ifd.get("PhotographicSensitivity")

    return {
        "camera": " ".join(str(x) for x in [ifd0.get("Make"), ifd0.get("Model")] if x).strip() or None,
        "lens": exif_ifd.get("LensModel") or None,
        "focalLength": format_decimal(focal, "{}mm", 0) if focal else None,
        "aperture": format_decimal(fnum, "f/{}", 1) if fnum else None,
        "shutter": format_shutter(exposure) if exposure else None,
        "iso": int(iso) if iso else None,
        "date": (exif_ifd.get("DateTimeOriginal") or ifd0.get("DateTime") or "").replace(":", "-", 2) or None,
        "lat": lat,
        "lon": lon,
    }


def build():
    os.makedirs(WEB_DIR, exist_ok=True)
    entries = []

    files = sorted(
        f for f in os.listdir(SRC_DIR)
        if f.lower().endswith((".jpg", ".jpeg")) and os.path.isfile(os.path.join(SRC_DIR, f))
    )

    if not files:
        print(f"No .jpg/.jpeg files found in {SRC_DIR}")
        return

    for fname in files:
        path = os.path.join(SRC_DIR, fname)
        stem = os.path.splitext(fname)[0]
        img = Image.open(path)
        meta = extract_exif(img)

        rgb = ImageOps.exif_transpose(img).convert("RGB")

        thumb = rgb.copy()
        thumb.thumbnail((THUMB_MAX, THUMB_MAX), Image.LANCZOS)
        thumb_name = f"{stem}-thumb.jpg"
        thumb.save(os.path.join(WEB_DIR, thumb_name), "JPEG", quality=JPEG_QUALITY)

        full = rgb.copy()
        full.thumbnail((FULL_MAX, FULL_MAX), Image.LANCZOS)
        full_name = f"{stem}-full.jpg"
        full.save(os.path.join(WEB_DIR, full_name), "JPEG", quality=JPEG_QUALITY)

        entry = {
            "id": stem,
            "thumb": f"photos/web/{thumb_name}",
            "full": f"photos/web/{full_name}",
            **meta,
        }
        if entry["lat"] is not None and entry["lon"] is not None:
            entry["mapUrl"] = f"https://www.openstreetmap.org/?mlat={entry['lat']}&mlon={entry['lon']}#map=14/{entry['lat']}/{entry['lon']}"
        else:
            entry["mapUrl"] = None

        entries.append(entry)
        print(f"processed {fname}: camera={entry['camera']!r} lens={entry['lens']!r} gps={entry['lat'], entry['lon']}")

    with open(MANIFEST_PATH, "w", encoding="utf-8") as f:
        json.dump(entries, f, indent=2, ensure_ascii=False)

    print(f"\nwrote {MANIFEST_PATH} ({len(entries)} photos)")


if __name__ == "__main__":
    build()
