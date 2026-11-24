"""What is inside the case and where: the layers from back to front and the plan of the board.

From the chest outwards: back cover, cell, board, the parts on the board's outer face, stone.
The board is an ellipse. The microphones are bottom-port parts, so they hang from the inner
face of the board with their hole through it, one at each tip of the oval; the cell lies
between them, centred, and the strip it leaves free along one side carries the switch, which
is pressed through the rim, and the spring contacts to the pads on the back.
"""
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

import yaml

from .params import CaseParams

ROOT = Path(__file__).resolve().parents[2]

SWELL = 0.08          # cell thickness growth over its life
CELL_PAD = 0.10       # adhesive under the cell
CELL_GAP = 0.20       # around the cell, each side
BOARD_CLEAR = 0.30    # between the swollen cell and the board (solder joints, tolerance)
TOP_GAP = 0.20        # between the tallest part and the underside of the stone
MIC_TIP = 0.90        # microphone to the tip of the board
MIC_EDGE = 0.25       # microphone corners to the board edge
MIC_CELL_GAP = 0.30   # microphone to the pads of the cell tabs
SIDE_EDGE = 0.50      # switch to the board edge
SIDE_GAP = 0.30       # switch to the cell
ANTENNA_ZONE = (7.0, 3.4)   # along the edge, and inwards from it: no copper on any layer
SOC_SHIFT = 4.6       # the microcontroller sits this far from the centre, which is the light's
PART_SPACING = 0.15   # between the land patterns of small parts
FINE_PITCH_MARGIN = 0.30
PACKING = 0.50        # share of the free board area that small parts may take; the rest is for tracks
MIN_MIC_DISTANCE = 20.0
EDGE = 0.40           # copper to the board edge
SMALL = {"passive0201", "passive0402", "passive0603", "inductor0402", "nfet", "xtal32m", "xtal32k", "inductor", "protector"}


@lru_cache
def load_parts() -> dict:
    return yaml.safe_load((ROOT / "parts" / "parts.yaml").read_text())


def body_of(c) -> str | None:
    """Key in parts.yaml of the body a circuit component occupies; None if it occupies none."""
    name, value, pkg = c.sym.name, c.value, c.fields.get("Package", "")
    if c.sym.virtual:
        return None
    by_value = {"nRF54L15": "soc", "nPM1304": "pmic", "W25Q512NW": "flash", "T5838": "mic", "S-82A1A": "protector"}
    by_symbol = {"SW": "button", "LED": "led", "ANTENNA": "antenna", "NMOS": "nfet", "CONTACT": "contact",
                 "PAD": "testpad", "CELL": "celltabs", "XTAL4": "xtal32m"}
    if value in by_value:
        return by_value[value]
    if name in by_symbol:
        return by_symbol[name]
    if name == "XTAL":
        return "xtal32k"
    if pkg == "0806":
        return "inductor"
    if name == "L" and value == "4.7uH":
        return "inductor0402"
    return {"0603": "passive0603", "0402": "passive0402"}.get(pkg, "passive0201")


@dataclass(frozen=True)
class Placed:
    name: str
    part: str | None      # key in parts.yaml; None for a keep-out
    face: str             # "top" (towards the stone), "bottom" (towards the cell) or "both"
    x: float              # rectangle on the board, origin at a corner of the box around the ellipse
    y: float
    w: float
    h: float
    rot: int = 0          # degrees, as KiCad turns a footprint

    @property
    def centre(self) -> tuple[float, float]:
        return self.x + self.w / 2, self.y + self.h / 2

    @property
    def area(self) -> float:
        return self.w * self.h

    def overlaps(self, o: "Placed") -> bool:
        if "both" not in (self.face, o.face) and self.face != o.face:
            return False
        return self.x < o.x + o.w and o.x < self.x + self.w and self.y < o.y + o.h and o.y < self.y + self.h


def in_ellipse(x: float, y: float, length: float, width: float, inset: float = 0.0) -> bool:
    """Inside the ellipse drawn in the box 0..length, 0..width, moved inwards by inset."""
    a, b = length / 2 - inset, width / 2 - inset
    return a > 0 and b > 0 and ((x - length / 2) / a) ** 2 + ((y - width / 2) / b) ** 2 <= 1 + 1e-9


def half_chord(y: float, length: float, width: float, inset: float = 0.0) -> float:
    """Half the length of the ellipse along X at height y; 0 outside it."""
    a, b = length / 2 - inset, width / 2 - inset
    t = 1 - ((y - width / 2) / b) ** 2
    return a * t ** 0.5 if t > 0 else 0.0


def on_board(pl: Placed, p: CaseParams, inset: float = 0.0) -> bool:
    """Every corner inside the board outline."""
    L, W = p.board
    return all(in_ellipse(x, y, L, W, inset)
               for x in (pl.x, pl.x + pl.w) for y in (pl.y, pl.y + pl.h))


def mic_centres(p: CaseParams, parts) -> tuple[float, float]:
    """Along the board: microphone A at the tip with the bail, B at the opposite one."""
    L, _ = p.board
    m = MIC_TIP + parts["parts"]["mic"]["size"][0] / 2
    return m, L - m


def cell_limits(p: CaseParams, parts) -> tuple[float, float]:
    """The longest and the widest cell that can lie centred under the board.

    Along the board it stops before the pads of its own tabs, which stop before microphone B.
    Across, it leaves the strip where the switch sits."""
    L, W = p.board
    _, mic_b = mic_centres(p, parts)
    tabs = parts["parts"]["celltabs"]["size"][0]
    end = mic_b - parts["parts"]["mic"]["size"][0] / 2 - MIC_CELL_GAP - tabs - CELL_GAP
    side = W - SIDE_EDGE - parts["parts"]["button"]["size"][1] - SIDE_GAP
    return 2 * (end - L / 2), 2 * (side - W / 2 - CELL_GAP)


def cell_in_cavity(p: CaseParams, length: float, width: float) -> bool:
    """A centred cell, with its gap, clears the rim all round."""
    cl, cw, _ = p.cavity
    return in_ellipse(cl / 2 + length / 2 + CELL_GAP, cw / 2 + width / 2 + CELL_GAP, cl, cw)


def layout(p: CaseParams, parts=None, cell_length: float | None = None) -> list[Placed]:
    """Every part whose place is decided by the case, and every keep-out. The board generator
    (electrical/gen/board.py) takes these positions and arranges the remaining parts around them.

    Seen from the front with the bail up, X runs downwards and Y to the left: the antenna is on
    one long edge of the board, the switch and the contacts on the other."""
    parts = parts or load_parts()
    L, W = p.board
    cx, cy = L / 2, W / 2
    out = []

    def part(name, key, face, x, y, margin=0.0, rot=0):
        w, h = parts["parts"][key]["size"][:2]          # as placed: parts.yaml gives the microphone turned
        out.append(Placed(name, key, face, x - w / 2 - margin, y - h / 2 - margin, w + 2 * margin, h + 2 * margin, rot))

    def keep(name, face, x, y, w, h):
        out.append(Placed(name, None, face, x, y, w, h))

    # the two tips: a microphone under each, on the long axis
    mic_a, mic_b = mic_centres(p, parts)
    for name, x in (("A", mic_a), ("B", mic_b)):
        part(f"microphone {name}", "mic", "bottom", x, cy, rot=90)
        keep(f"microphone {name} gasket", "top", x - 1.5, cy - 1.5, 3.0, 3.0)
    # the light: under the very middle of the stone, so that the glow has its centre there.
    # The microcontroller makes room for it by sitting beside it, towards the bail.
    part("light", "led", "top", cx, cy)
    soc_x = cx - SOC_SHIFT
    # one long side: the antenna, at the edge in front of the microcontroller, with nothing in
    # copper around it
    zl, zd = ANTENNA_ZONE
    keep("antenna keep-out", "both", soc_x - zl / 2, 0.0, zl, zd)
    part("antenna", "antenna", "top", soc_x, 1.7)
    # the other long side, under the board: the switch, pressed through the rim, between two
    # pairs of spring contacts
    sw = parts["parts"]["button"]["size"][1]
    part("button", "button", "bottom", cx, W - SIDE_EDGE - sw / 2)
    for name, dx in (("charge +", -6.5), ("charge -", -4.0), ("SWDIO", 4.0), ("SWDCLK", 6.5)):
        part(f"contact {name}", "contact", "bottom", cx + dx, W - 2.6)
    # the cell tabs come out at the end towards microphone B
    half = (cell_length if cell_length is not None else cell_limits(p, parts)[0]) / 2
    part("cell tabs", "celltabs", "bottom", cx + half + CELL_GAP + parts["parts"]["celltabs"]["size"][0] / 2, cy)
    # on the outer face. The microcontroller is turned so that its antenna pin faces the antenna
    # and has the half of the board towards the bail to itself. The other half holds the power
    # chip, nearer the antenna edge and next to the cell tabs, and the flash below it, on the side
    # of the microcontroller's fast-SPI pins.
    soc = parts["parts"]["soc"]["size"][0] / 2 + FINE_PITCH_MARGIN
    pmic = parts["parts"]["pmic"]["size"][0] / 2 + FINE_PITCH_MARGIN
    fl, fw = parts["parts"]["flash"]["size"][:2]
    part("microcontroller", "soc", "top", soc_x, zd + 4.1 + soc, margin=FINE_PITCH_MARGIN, rot=90)
    part("flash", "flash", "top", cx + 1.6 + fl / 2, cy + 0.6 + fw / 2)
    part("power chip", "pmic", "top", cx + 1.6 + pmic, cy + 0.6 - 0.9 - pmic, margin=FINE_PITCH_MARGIN)
    for i, name in enumerate(("nRESET", "UART TX", "UART RX", "1V8", "GND", "VBAT", "VBUS")):
        part(f"test pad {name}", "testpad", "top", cx + 1.5 * (i - 3), W - 2.6)
    return out


def small_area(bodies: list[str], parts=None) -> float:
    """Board area the small parts need, each with its share of spacing."""
    parts = parts or load_parts()
    total = 0.0
    for b in bodies:
        w, h = parts["parts"][b]["size"][:2]
        total += (w + PART_SPACING) * (h + PART_SPACING)
    return total
