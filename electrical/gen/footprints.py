"""Footprints: the project library in electrical/kicad/pendant.pretty.

Standard packages are copies of KiCad's stock footprints (QFN, WSON, crystals, chip parts). The others are written here
from the manufacturers' land-pattern drawings; `status` says how far each was checked.
Every footprint has its long side along X.
"""
import re
from functools import lru_cache
from pathlib import Path

LIB = Path(__file__).resolve().parents[1] / "kicad" / "pendant.pretty"
LIB_NAME = "pendant"


def _grid(rows: str, cols: int, px: float, py: float, skip=(), only=None):
    """Ball positions for a grid named A1.. with A1 at the top left, seen from above."""
    out = {}
    for r, row in enumerate(rows):
        for c in range(cols):
            name = f"{row}{c + 1}"
            if name in skip or (only is not None and name not in only):
                continue
            out[name] = (round((c - (cols - 1) / 2) * px, 4), round((r - (len(rows) - 1) / 2) * py, 4))
    return out


def _balls(positions, d):
    return [(n, "circle", x, y, d, d) for n, (x, y) in positions.items()]


# name: body (x, y), pads [(number, shape, x, y, w, h)], extras, status
CUSTOM = {
    # TDK DS-000383 figure 36, moved so that the origin is the body centre (port at +0.71).
    "T5838": dict(
        body=(3.5, 2.65),
        pads=[("7", "rect", -1.364, -0.8375, 0.522, 0.725), ("6", "rect", -0.542, -0.8375, 0.522, 0.725),
              ("1", "rect", -1.364, 0.8375, 0.522, 0.725), ("2", "rect", -0.542, 0.8375, 0.522, 0.725),
              ("5", "rect", 1.475, -1.05, 0.30, 0.30), ("4", "rect", 1.475, 1.05, 0.30, 0.30)],
        ring=("3", 0.71, 0.0, 1.025, 1.625), hole=(0.71, 0.0, 0.6),
        status="pad sizes and positions verified; pin-to-pad mapping read by matching two figures"),
    # A side-push switch: the plunger leaves the body on its +Y side, towards the board edge.
    "Side_Switch": dict(
        body=(3.5, 2.9),
        pads=[("1", "rect", -1.9, -0.6, 0.9, 1.0), ("2", "rect", 1.9, -0.6, 0.9, 1.0)],
        status="placeholder until the switch is chosen"),
    # ABLIC PV006-A-L-SD-1.0.
    "DFN-6_1414": dict(
        body=(1.4, 1.4),
        pads=[("1", "rect", -0.5, 0.625, 0.2, 0.55), ("2", "rect", 0.0, 0.625, 0.2, 0.55), ("3", "rect", 0.5, 0.625, 0.2, 0.55),
              ("4", "rect", 0.5, -0.625, 0.2, 0.55), ("5", "rect", 0.0, -0.625, 0.2, 0.55), ("6", "rect", -0.5, -0.625, 0.2, 0.55),
              ("", "rect", 0.0, 0.0, 0.8, 0.15)],
        status="land sizes verified; pin order around the package assumed"),
    "Antenna_1608": dict(
        body=(1.6, 0.8), pads=[("1", "rect", -0.6, 0.0, 0.4, 0.8), ("", "rect", 0.6, 0.0, 0.4, 0.8)],
        status="placeholder until the antenna is chosen"),
    "Spring_Contact": dict(body=(2.0, 1.5), pads=[("1", "rect", 0, 0, 1.6, 1.1)],
                           status="placeholder until the contact is chosen"),
    "Pad_Test_D1.0": dict(body=(1.0, 1.0), pads=[("1", "circle", 0, 0, 1.0, 1.0)], paste=False, status="design choice"),
    "Cell_Tabs": dict(
        body=(1.6, 4.4), pads=[("1", "rect", 0.0, -1.2, 1.2, 1.6), ("2", "rect", 0.0, 1.2, 1.2, 1.6)], paste=False,
        status="placeholder until the cell drawing is in hand"),
}


def _text(name: str, fp: dict) -> str:
    bx, by = fp["body"][0] / 2, fp["body"][1] / 2
    layers = '"F.Cu" "F.Mask" "F.Paste"' if fp.get("paste", True) else '"F.Cu" "F.Mask"'
    mask = f' (solder_mask_margin {fp["mask"]})' if "mask" in fp else ""
    out = [f'(footprint "{name}" (version 20241229) (generator "pendant_gen") (layer "F.Cu")',
           f'\t(descr "{fp["status"]}")',
           '\t(property "Reference" "REF**" (at 0 0 0) (layer "F.Fab") (hide yes) (effects (font (size 0.3 0.3) (thickness 0.05))))',
           f'\t(property "Value" "{name}" (at 0 0 0) (layer "F.Fab") (hide yes) (effects (font (size 0.3 0.3) (thickness 0.05))))',
           '\t(attr smd)',
           f'\t(fp_rect (start {-bx} {-by}) (end {bx} {by}) (stroke (width 0.05) (type solid)) (fill no) (layer "F.Fab"))']
    ex, ey = extent_of(fp)
    out.append(f'\t(fp_rect (start {-ex / 2 - 0.05:.3f} {-ey / 2 - 0.05:.3f}) (end {ex / 2 + 0.05:.3f} {ey / 2 + 0.05:.3f}) '
               '(stroke (width 0.05) (type solid)) (fill no) (layer "F.CrtYd"))')
    for num, shape, x, y, w, h in fp["pads"]:
        out.append(f'\t(pad "{num}" smd {shape} (at {x} {y}) (size {w} {h}) (layers {layers}){mask})')
    if "ring" in fp:        # annular ground pad around the sound port, drawn as a thick circle
        num, x, y, d_in, d_out = fp["ring"]
        r, width = (d_in + d_out) / 4, (d_out - d_in) / 2
        out.append(f'\t(pad "{num}" smd custom (at {x - r} {y}) (size {width} {width}) (layers "F.Cu" "F.Mask")'
                   f' (options (clearance outline) (anchor circle))'
                   f' (primitives (gr_circle (center {r} 0) (end {2 * r} 0) (width {width}) (fill no))))')
    if "hole" in fp:
        x, y, d = fp["hole"]
        out.append(f'\t(pad "" np_thru_hole circle (at {x} {y}) (size {d} {d}) (drill {d}) (layers "*.Cu" "*.Mask"))')
    return "\n".join(out) + "\n)\n"


def extent_of(fp: dict) -> tuple[float, float]:
    xs = [fp["body"][0] / 2] + [abs(x) + w / 2 for _, _, x, _, w, _ in fp["pads"]]
    ys = [fp["body"][1] / 2] + [abs(y) + h / 2 for _, _, _, y, _, h in fp["pads"]]
    if "ring" in fp:
        _, x, y, _, d = fp["ring"]
        xs.append(abs(x) + d / 2), ys.append(abs(y) + d / 2)
    return 2 * max(xs), 2 * max(ys)


def write_custom():
    LIB.mkdir(parents=True, exist_ok=True)
    for name, fp in CUSTOM.items():
        (LIB / f"{name}.kicad_mod").write_text(_text(name, fp))


PAD = re.compile(r'\(pad\s+"[^"]*"\s+\w+\s+\w+\s*\(at\s+([-\d.]+)\s+([-\d.]+)[^)]*\)\s*\(size\s+([-\d.]+)\s+([-\d.]+)\)')
FAB = re.compile(r'\(fp_rect\s*\(start\s+([-\d.]+)\s+([-\d.]+)\)\s*\(end\s+([-\d.]+)\s+([-\d.]+)\).*?\(layer\s+"([^"]+)"\)', re.S)


# Bodies larger than their pads, for stock footprints whose outline is not a plain rectangle in the file.
BODY = {"WSON-8-1EP_8x6mm_P1.27mm_EP3.4x4.3mm": (8.0, 6.0)}


@lru_cache(maxsize=None)
def extent(name: str) -> tuple[float, float]:
    """Width and height of the copper and body of a footprint in the library."""
    if name in CUSTOM:
        return extent_of(CUSTOM[name])
    text = (LIB / f"{name}.kicad_mod").read_text()
    xs, ys = [], []
    for x, y, w, h in PAD.findall(text):
        xs.append(abs(float(x)) + float(w) / 2), ys.append(abs(float(y)) + float(h) / 2)
    for x0, y0, x1, y1, layer in FAB.findall(text):
        if layer == "F.Fab":
            xs += [abs(float(x0)), abs(float(x1))]
            ys += [abs(float(y0)), abs(float(y1))]
    assert xs, name
    bw, bh = BODY.get(name, (0.0, 0.0))
    return max(round(2 * max(xs), 3), bw), max(round(2 * max(ys), 3), bh)


def pads_of(name: str) -> list[tuple[str, float, float, float, float]]:
    """(number, x, y, width, height) of every numbered pad of a footprint, in its own coordinates."""
    if name in CUSTOM:
        fp = CUSTOM[name]
        out = [(n, x, y, w, h) for n, _, x, y, w, h in fp["pads"] if n]
        if "ring" in fp:
            n, x, y, d_in, d_out = fp["ring"]         # KiCad's position of this pad is its anchor, on the ring
            out.append((n, x - (d_in + d_out) / 4, y, d_out, d_out))
        return out
    text = (LIB / f"{name}.kicad_mod").read_text()
    return [(n, float(x), float(y), float(w), float(h)) for n, x, y, w, h in NUMBERED.findall(text) if n]


NUMBERED = re.compile(r'\(pad\s+"([^"]*)"\s+smd\s+\w+\s*\(at\s+([-\d.]+)\s+([-\d.]+)[^)]*\)\s*\(size\s+([-\d.]+)\s+([-\d.]+)\)')


def footprint_of(c) -> str | None:
    """Footprint name for a circuit component."""
    if c.sym.virtual:
        return None
    by_value = {"nRF54L15": "QFN-48-1EP_6x6mm_P0.4mm_EP4.6x4.6mm", "nPM1304": "QFN-32-1EP_5x5mm_P0.5mm_EP3.45x3.45mm",
                "W25Q512NW": "WSON-8-1EP_8x6mm_P1.27mm_EP3.4x4.3mm", "T5838": "T5838", "S-82A1A": "DFN-6_1414"}
    if c.value in by_value:
        return by_value[c.value]
    sym, pkg = c.sym.name, c.fields.get("Package", "")
    if sym in ("XTAL", "XTAL4"):
        return "Crystal_SMD_2016-4Pin_2.0x1.6mm" if sym == "XTAL4" else "Crystal_SMD_2012-2Pin_2.0x1.2mm"
    simple = {"SW": "Side_Switch", "LED": "LED_0402_1005Metric", "ANTENNA": "Antenna_1608", "NMOS": "SOT-883",
              "CELL": "Cell_Tabs", "TVS": "D_0201_0603Metric", "D": "D_0201_0603Metric", "FB": "L_0201_0603Metric",
              "PAD": "Pad_Test_D1.0", "CONTACT": "Spring_Contact"}
    if sym in simple:
        return simple[sym]
    if sym == "L":
        return {"0806": "L_0805_2012Metric", "0402": "L_0402_1005Metric"}.get(pkg, "L_0201_0603Metric")
    prefix = "C" if sym == "C" else "R"
    return f"{prefix}_{ {'0603': '0603_1608Metric', '0402': '0402_1005Metric'}.get(pkg, '0201_0603Metric') }"


if __name__ == "__main__":
    write_custom()
    for f in sorted(LIB.glob("*.kicad_mod")):
        print(f"{f.stem:<36} {extent(f.stem)}")
