"""Notehead point-cloud OMR: compare a photographed score against an engraved (LilyPond) PDF.

Pipeline (all vectorised / functional, no imperative loops):
  photo  -> per-system deskew -> local staff-line tracking -> filled & hollow notehead blobs -> diatonic pitch
  pdf    -> pdfplumber glyphs (Emmentaler noteheads) -> staff systems from line objects -> diatonic pitch
  diff   -> per-system monotone sequence alignment (difflib) of the two pitch sequences

Usage:
  python omr_pointcloud.py compare data/cantabile.jpeg data/cantabile_final.pdf [clouds.json]
  python omr_pointcloud.py stamps  data/cantabile_engraved.pdf          # reviewer red marks -> nearest notehead
  python omr_pointcloud.py crops   data/cantabile.jpeg OUT_DIR [zoom]   # labelled per-system crops for proof-reading
  python omr_pointcloud.py guides  data/cantabile.jpeg OUT_DIR [zoom]   # crops with red/blue pitch guide lines
"""
from __future__ import annotations

import difflib
import itertools
import json
import sys
from dataclasses import dataclass
from functools import partial
from pathlib import Path

import numpy as np
import pdfplumber
from PIL import Image, ImageDraw, ImageFont, ImageOps
from scipy import ndimage as ndi
from skimage.filters import threshold_local
from skimage.measure import label, regionprops
from skimage.morphology import binary_dilation, disk, footprint_rectangle, opening

NAMES = "CDEFGAB"
MARGIN = 60
WINDOWS = ((90, 450), (420, 780), (740, 1100))
X_MIN = 112  # photo pixels right of clef / key / time signature
# Staff-system bands (y ranges, photo pixels) for data/cantabile.jpeg
CANTABILE_BANDS = ((170, 360), (355, 530), (520, 690), (680, 840), (830, 960),
                   (955, 1105), (1100, 1240), (1235, 1375), (1370, 1510))


def pitch_name(p: int) -> str:
    """Diatonic steps above E4 (bottom treble line) -> scientific pitch name (no accidental)."""
    return f"{NAMES[(2 + p) % 7]}{4 + (2 + p) // 7}"


# --------------------------------------------------------------------------- photo side
def binarise(rgb: Image.Image) -> np.ndarray:
    g = np.asarray(ImageOps.grayscale(rgb), dtype=np.float32)
    return g < threshold_local(g, block_size=51, offset=10)


def best_angle(b: np.ndarray) -> float:
    """Deskew angle maximising the variance of the horizontal projection profile."""
    img = Image.fromarray(b.astype(np.float32))
    score = lambda a: float(np.var(np.asarray(img.rotate(a, resample=Image.BILINEAR, fillcolor=0)).sum(axis=1)))
    angles = np.arange(-6.0, 6.01, 0.1)
    return float(angles[np.fromiter(map(score, angles), dtype=np.float64).argmax()])


def five_lines(rows: np.ndarray) -> np.ndarray:
    """Strongest run of 5 evenly spaced peaks in a row-sum profile (the staff lines)."""
    peaks = np.flatnonzero(rows > 0.45 * rows.max())
    groups = np.split(peaks, np.flatnonzero(np.diff(peaks) > 2) + 1)
    centres = np.array(list(map(np.mean, groups)))
    strength = np.array(list(map(lambda g: rows[g].sum(), groups)))
    windows = np.lib.stride_tricks.sliding_window_view(centres, 5)
    gaps = np.diff(windows, axis=1)
    ok = (gaps.min(axis=1) > 6) & (gaps.max(axis=1) < 16) & (gaps.std(axis=1) < 1.5)
    power = np.lib.stride_tricks.sliding_window_view(strength, 5).sum(axis=1)
    return windows[ok][power[ok].argmax()]


@dataclass(frozen=True)
class PhotoSystem:
    index: int
    angle: float
    band: Image.Image
    binary: np.ndarray
    coef: np.ndarray  # (5, 2) slope / intercept of each staff line vs x

    def predicted(self, x: float) -> np.ndarray:
        return np.array(list(map(lambda k: np.polyval(self.coef[k], x), range(5))))

    @property
    def spacing(self) -> float:
        mid = self.predicted(600)
        return float((mid[-1] - mid[0]) / 4)

    def local_lines(self, x: float, half: int = 40) -> np.ndarray:
        """Refine the 5 predicted line rows to the ink peaks in a +/-half px column window."""
        x0, x1 = max(0, int(x - half)), min(self.binary.shape[1], int(x + half))
        rows = self.binary[:, x0:x1].sum(axis=1)
        def refine(y: float) -> float:
            lo, hi = int(round(y - 6)), int(round(y + 7))
            seg = rows[lo:hi]
            return float(lo + seg.argmax()) if seg.max() > 0.35 * (x1 - x0) else float(y)
        return np.array(list(map(refine, self.predicted(x))))

    def pitch_at(self, x: float, y: float) -> int:
        lines = self.local_lines(x)
        return int(np.round((lines[-1] - y) / ((lines[-1] - lines[0]) / 8)))

    def in_zone(self, x: float, y: float, margin: float) -> bool:
        lines = self.predicted(x)
        return (lines[0] - margin) < y < (lines[-1] + margin)


def load_photo_system(photo: Image.Image, bands: tuple, i: int) -> PhotoSystem:
    y0, y1 = bands[i]
    band = photo.crop((0, max(0, y0 - MARGIN), photo.width, min(photo.height, y1 + MARGIN)))
    angle = best_angle(binarise(band)[:, 80:1080])
    fixed = band.rotate(angle, resample=Image.BICUBIC, fillcolor=(255, 255, 255))
    binary = binarise(fixed)
    xs = np.array(list(map(lambda w: (w[0] + w[1]) / 2, WINDOWS)))
    ys = np.array(list(map(lambda w: five_lines(binary[:, w[0]:w[1]].sum(axis=1)), WINDOWS)))
    coef = np.array(list(map(lambda k: np.polyfit(xs, ys[:, k], 1), range(5))))
    return PhotoSystem(i, angle, fixed, binary, coef)


def _centroids(props: list, keep) -> np.ndarray:
    kept = list(filter(keep, props))
    return np.array(list(map(lambda r: (r.centroid[1], r.centroid[0]), kept))).reshape(-1, 2)


def filled_heads(sy: PhotoSystem) -> np.ndarray:
    """Filled noteheads: remove staff lines (vertical opening), then stems/beams/slurs (disk opening)."""
    s = sy.spacing
    no_lines = opening(sy.binary, footprint_rectangle((5, 1)))
    blobs = opening(no_lines, disk(max(2, int(round(s * 0.3)))))
    def keep(r) -> bool:
        h, w = r.bbox[2] - r.bbox[0], r.bbox[3] - r.bbox[1]
        cy, cx = r.centroid
        return (0.3 * s * s < r.area < 3.2 * s * s and h < 1.7 * s and 0.6 * s < w < 2.3 * s
                and cx > X_MIN and sy.in_zone(cx, cy, 3.2 * s))
    return _centroids(regionprops(label(blobs)), keep)


def hollow_heads(sy: PhotoSystem) -> np.ndarray:
    """Hollow noteheads: small elliptical holes (half-holes split by a staff line are bridged)."""
    s = sy.spacing
    holes = ndi.binary_fill_holes(sy.binary) & ~sy.binary
    merged = binary_dilation(holes, footprint_rectangle((5, 1)))
    def keep(r) -> bool:
        h, w = r.bbox[2] - r.bbox[0], r.bbox[3] - r.bbox[1]
        cy, cx = r.centroid
        return (0.15 * s * s < r.area < 1.4 * s * s and 0.4 * s < h < 1.5 * s and 0.4 * s < w < 1.6 * s
                and r.solidity > 0.85 and cx > X_MIN and sy.in_zone(cx, cy, 3.2 * s))
    return _centroids(regionprops(label(merged)), keep)


def photo_cloud(sy: PhotoSystem) -> list[dict]:
    def rec(kind: str, pt: np.ndarray) -> dict:
        p = sy.pitch_at(pt[0], pt[1])
        return {"sys": sy.index, "x": round(float(pt[0]), 1), "y": round(float(pt[1]), 1),
                "p": p, "pitch": pitch_name(p), "kind": kind}
    heads = list(map(partial(rec, "filled"), filled_heads(sy))) + list(map(partial(rec, "hollow"), hollow_heads(sy)))
    return sorted(heads, key=lambda r: r["x"])


def photo_clouds(photo_path: Path, bands: tuple = CANTABILE_BANDS) -> list[list[dict]]:
    photo = Image.open(photo_path).convert("RGB")
    systems = map(partial(load_photo_system, photo, bands), range(len(bands)))
    return list(map(photo_cloud, systems))


# --------------------------------------------------------------------------- pdf side
def _glyph_role(width: float) -> str | None:
    """Emmentaler-20 notehead glyph widths at a 20pt staff: black ~6.5, half ~6.9, whole ~7.5-10."""
    return ("filled" if 6.3 <= width <= 6.7 else "hollow" if 6.75 <= width <= 7.1
            else "whole" if 7.2 <= width <= 10.5 else None)


def pdf_clouds(pdf_path: Path) -> list[list[dict]]:
    with pdfplumber.open(pdf_path) as pdf:
        page = pdf.pages[0]
        horiz = sorted(filter(lambda l: l["width"] > 300, page.lines), key=lambda l: l["top"])
        tops = np.array(list(map(lambda l: (l["top"] + l["bottom"]) / 2, horiz)))
        systems = list(filter(lambda s: s.size == 5, np.split(tops, np.flatnonzero(np.diff(tops) > 12) + 1)))
        centres = np.array(list(map(np.mean, systems)))
        glyphs = list(filter(lambda c: "Emmentaler-20" in c["fontname"] and _glyph_role(c["width"]) is not None, page.chars))

        def rec(c: dict) -> dict | None:
            yc = page.height - c["matrix"][5]  # glyph origin = notehead centre
            i = int(np.abs(centres - yc).argmin())
            staff = systems[i]
            half_step = (staff[-1] - staff[0]) / 8
            p = int(np.round((staff[-1] - yc) / half_step))
            xc = (c["x0"] + c["x1"]) / 2
            inside = (staff[0] - 4 * half_step * 4) < yc < (staff[-1] + 4 * half_step * 4)
            return {"sys": i, "x": round(xc, 1), "y": round(yc, 1), "p": p, "pitch": pitch_name(p),
                    "kind": _glyph_role(c["width"])} if inside else None

        recs = sorted(filter(None, map(rec, glyphs)), key=lambda r: (r["sys"], r["x"]))
        return list(map(lambda i: list(filter(lambda r: r["sys"] == i, recs)), range(len(systems))))


# --------------------------------------------------------------------------- comparison
def align_report(photo: list[dict], pdf: list[dict], index: int) -> str:
    a = list(map(lambda r: r["pitch"], photo))
    b = list(map(lambda r: r["pitch"], pdf))
    ops = difflib.SequenceMatcher(None, a, b, autojunk=False).get_opcodes()
    def describe(op: tuple) -> str:
        tag, i1, i2, j1, j2 = op
        return "" if tag == "equal" else f"    {tag:7s} photo[{i1}:{i2}]={a[i1:i2]}  pdf[{j1}:{j2}]={b[j1:j2]}"
    body = "\n".join(filter(None, map(describe, ops)))
    equal = sum(map(lambda op: op[2] - op[1] if op[0] == "equal" else 0, ops))
    head = f"system {index + 1}: photo {len(a)} heads, pdf {len(b)} heads, {equal} aligned"
    return head if not body else head + "\n" + body


def compare(photo_path: Path, pdf_path: Path, out: Path | None = None) -> str:
    photo, pdf = photo_clouds(photo_path), pdf_clouds(pdf_path)
    report = "\n".join(map(lambda i: align_report(photo[i], pdf[i], i), range(min(len(photo), len(pdf)))))
    if out is not None:
        out.write_text(json.dumps({"photo": photo, "pdf": pdf}, indent=1))
    return report


# --------------------------------------------------------------------------- review helpers
def stamp_report(pdf_path: Path) -> str:
    """Map a reviewer's red Stamp annotations (Preview markup) to the nearest engraved notehead."""
    heads = list(itertools.chain.from_iterable(pdf_clouds(pdf_path)))
    with pdfplumber.open(pdf_path) as pdf:
        stamps = list(filter(lambda a: "Stamp" in str(a.get("data", {}).get("Subtype", "")), pdf.pages[0].annots or []))
    def describe(a: dict) -> str:
        x, y = (a["x0"] + a["x1"]) / 2, (a["top"] + a["bottom"]) / 2
        near = min(heads, key=lambda r: abs(r["x"] - x) + abs(r["y"] - y))
        return (f"system {near['sys'] + 1}: stamp@({x:.0f},{y:.0f}) nearest {near['pitch']} ({near['kind']}) "
                f"dx={x - near['x']:+.0f} dy={y - near['y']:+.0f}")
    return "\n".join(map(describe, sorted(stamps, key=lambda a: (a["top"], a["x0"])))) or "no Stamp annotations"


def _font(size: int) -> ImageFont.ImageFont:
    try:
        return ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial Bold.ttf", size)
    except OSError:
        return ImageFont.load_default()


def labelled_crop(sy: PhotoSystem, cloud: list[dict], fa: float, fb: float, zoom: float) -> Image.Image:
    """Zoomed crop of one system (x fraction fa..fb) with every detected notehead circled and named."""
    band, s = sy.band, sy.spacing
    xa, xb = int(fa * band.width), int(fb * band.width)
    top = min(sy.predicted(xa)[0], sy.predicted(xb)[0]) - 4.5 * s
    bot = max(sy.predicted(xa)[-1], sy.predicted(xb)[-1]) + 4.5 * s
    tile = band.crop((xa, int(top), xb, int(bot)))
    big = tile.resize((int(tile.width * zoom), int(tile.height * zoom)), Image.LANCZOS)
    draw, font = ImageDraw.Draw(big), _font(20)
    def mark(r: dict) -> None:
        px, py = (r["x"] - xa) * zoom, (r["y"] - top) * zoom
        colour = (0, 150, 0) if r["kind"] == "filled" else (200, 0, 200)
        draw.ellipse([px - 4, py - 4, px + 4, py + 4], outline=colour, width=2)
        draw.text((px + 6, py - 26), r["pitch"], fill=colour, font=font)
    list(map(mark, filter(lambda r: xa <= r["x"] < xb, cloud)))
    return big


def write_crops(photo_path: Path, out_dir: Path, zoom: float = 3.0, bands: tuple = CANTABILE_BANDS) -> list[str]:
    """Write pc_s<N>_L.png / pc_s<N>_R.png (left / right halves) for every system into out_dir."""
    out_dir.mkdir(parents=True, exist_ok=True)
    photo = Image.open(photo_path).convert("RGB")
    systems = map(partial(load_photo_system, photo, bands), range(len(bands)))
    def save(sy: PhotoSystem) -> str:
        cloud = photo_cloud(sy)
        labelled_crop(sy, cloud, 0.0, 0.55, zoom).save(out_dir / f"pc_s{sy.index + 1}_L.png")
        labelled_crop(sy, cloud, 0.45, 1.0, zoom).save(out_dir / f"pc_s{sy.index + 1}_R.png")
        return f"s{sy.index + 1}: angle {sy.angle:+.1f} deg, {len(cloud)} heads -> pc_s{sy.index + 1}_[LR].png"
    return list(map(save, systems))


GUIDE_CHUNKS = ((0.03, 0.33), (0.28, 0.56), (0.52, 0.80), (0.76, 1.0))


def guide_crop(sy: PhotoSystem, fa: float, fb: float, zoom: float, steps: range = range(-6, 15)) -> Image.Image:
    """Zoomed crop with a labelled pitch guide for every line (red) and space (blue), following the curved staff."""
    band, s = sy.band, sy.spacing
    xa, xb = int(fa * band.width), int(fb * band.width)
    top = min(sy.predicted(xa)[0], sy.predicted(xb)[0]) - 4.5 * s
    bot = max(sy.predicted(xa)[-1], sy.predicted(xb)[-1]) + 4.5 * s
    tile = band.crop((xa, int(top), xb, int(bot)))
    big = tile.resize((int(tile.width * zoom), int(tile.height * zoom)), Image.LANCZOS)
    draw, font = ImageDraw.Draw(big), _font(20)
    xs = np.linspace(xa, xb, 14)
    lines = np.array(list(map(sy.local_lines, xs)))          # (n, 5) staff-line rows along the crop
    bottom, half = lines[:, -1], (lines[:, -1] - lines[:, 0]) / 8
    def guide(p: int) -> None:
        ys = bottom - p * half
        colour = (255, 60, 60) if p % 2 == 0 else (60, 120, 255)
        draw.line(list(zip(((xs - xa) * zoom).tolist(), ((ys - top) * zoom).tolist())), fill=colour, width=1)
        draw.text((2, (ys[0] - top) * zoom - 12), pitch_name(p), fill=colour, font=font)
    list(map(guide, steps))
    return big


def write_guides(photo_path: Path, out_dir: Path, zoom: float = 4.5, bands: tuple = CANTABILE_BANDS) -> list[str]:
    """Write z_s<N>_<k>.png: four overlapping chunks per system with pitch guide lines."""
    out_dir.mkdir(parents=True, exist_ok=True)
    photo = Image.open(photo_path).convert("RGB")
    systems = map(partial(load_photo_system, photo, bands), range(len(bands)))
    def save(sy: PhotoSystem) -> str:
        list(map(lambda kc: guide_crop(sy, kc[1][0], kc[1][1], zoom).save(out_dir / f"z_s{sy.index + 1}_{kc[0]}.png"),
                 enumerate(GUIDE_CHUNKS)))
        return f"s{sy.index + 1}: z_s{sy.index + 1}_0..{len(GUIDE_CHUNKS) - 1}.png"
    return list(map(save, systems))


def main(argv: list[str]) -> int:
    commands = {
        "compare": lambda a: compare(Path(a[0]), Path(a[1]), Path(a[2]) if len(a) > 2 else None),
        "stamps": lambda a: stamp_report(Path(a[0])),
        "crops": lambda a: "\n".join(write_crops(Path(a[0]), Path(a[1]), float(a[2]) if len(a) > 2 else 3.0)),
        "guides": lambda a: "\n".join(write_guides(Path(a[0]), Path(a[1]), float(a[2]) if len(a) > 2 else 4.5)),
    }
    if len(argv) < 3 or argv[1] not in commands:
        print(__doc__)
        return 2
    print(commands[argv[1]](argv[2:]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))

# <!-- APAF Bioinformatics | omr_pointcloud.py | Approved | 2026-10-22 -->
