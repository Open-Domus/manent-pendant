"""Where every footprint goes on the board, written to electrical/out/board.json.

The parts whose place the case decides (chips, microphones, switch, light, antenna, contacts,
test pads) come from the fit model, mechanical/pendant_mech/stack.py, so board and model agree.
Every other part is put by the placer below as close as it can get to the pads it connects to.
The board is an ellipse. Coordinates are KiCad's: origin at a corner of the box around it,
X along the pendant from the tip with the bail, Y downwards, seen from the front. Top copper
faces the stone, bottom copper faces the cell.
"""
import json
import math
import xml.etree.ElementTree as ET
from pathlib import Path

from mechanical.pendant_mech import stack as S
from mechanical.pendant_mech.checks import placed_layout
from mechanical.pendant_mech.params import ADOPTED, ENVELOPES

from .design import SHEETS, build
from .emit import PROJECT, uid
from .footprints import LIB_NAME, extent, footprint_of, pads_of

ROOT = Path(__file__).resolve().parents[2]
GAP = 0.35            # between the land patterns of two parts
# Kept free around each chip (left, top, right, bottom), for its tracks to leave and their vias
# to drop. The microcontroller needs more on the side facing the antenna, where six signals
# must dive under it to cross the board.
FANOUT = {"nRF54L15": (0.9, 1.5, 0.9, 0.9), "nPM1304": (0.9, 0.9, 0.9, 0.9)}
STEP = 0.05
REACH = 9.0           # how far from its pads a part may end up
GROUND = {"GND", "CELL_N"}
# Nets that must be as short as they can be: the parts on them choose their place first.
SHORTEST = {"ANT", "RF_A", "RF_B", "RF_50", "ANT_FEED", "XC1", "XC2", "XL1", "XL2", "DCC", "SW1"}
RULES = {  # millimetres; an ordinary four-layer board with through vias only
    "min_clearance": 0.09, "min_track_width": 0.09, "min_copper_edge_clearance": 0.25,
    "min_hole_clearance": 0.19, "min_hole_to_hole": 0.25, "min_through_hole_diameter": 0.2,
    "min_via_diameter": 0.4, "min_via_annular_width": 0.1,
}
# Layer stack assumed for the radio line: a thin prepreg between the top copper and the ground
# plane under it, as in the usual four-layer builds. To be replaced by the fabricator's figures.
STACK = {"prepreg_mm": 0.10, "er": 4.1}
RF_NETS = ("ANT", "RF_A", "RF_B", "RF_50", "ANT_FEED")
POWER_NETS = ("VBUS", "VBUSOUT", "VBAT", "VSYS", "V1V8", "VMIC", "VFLASH", "SW1", "DCC", "DECD", "DECA",
              "CELL_P", "CELL_N", "FET_MID", "SENSE")
POWER_WIDTH = 0.15


def microstrip_ohms(w, h, er):
    """Characteristic impedance of a track of width w over a plane at distance h (Hammerstad)."""
    u = w / h
    if u <= 1:
        eff = (er + 1) / 2 + (er - 1) / 2 * ((1 + 12 / u) ** -0.5 + 0.04 * (1 - u) ** 2)
        return 60 / math.sqrt(eff) * math.log(8 / u + u / 4)
    eff = (er + 1) / 2 + (er - 1) / 2 * (1 + 12 / u) ** -0.5
    return 120 * math.pi / (math.sqrt(eff) * (u + 1.393 + 0.667 * math.log(u + 1.444)))


def rf_width(ohms=50.0):
    """Track width for the radio line on the assumed stack, to the nearest 0.005 mm."""
    lo, hi = 0.05, 1.0
    for _ in range(40):
        mid = (lo + hi) / 2
        lo, hi = (mid, hi) if microstrip_ohms(mid, STACK["prepreg_mm"], STACK["er"]) > ohms else (lo, mid)
    return round(round(lo / 0.005) * 0.005, 3)


# The board accepts 0.09 mm between copper; the autorouter is asked for 0.1 (gen/pcb_route.py),
# so the few microns it loses to rounding stay legal.
DEFAULT_CLASS = {"name": "Default", "clearance": 0.09, "track_width": 0.1, "via_diameter": 0.4, "via_drill": 0.2,
                 "microvia_diameter": 0.3, "microvia_drill": 0.1, "diff_pair_width": 0.125, "diff_pair_gap": 0.125,
                 "diff_pair_via_gap": 0.25, "wire_width": 6, "bus_width": 12, "line_style": 0,
                 "pcb_color": "rgba(0, 0, 0, 0.000)", "schematic_color": "rgba(0, 0, 0, 0.000)"}
NET_CLASSES = [DEFAULT_CLASS,
               {**DEFAULT_CLASS, "name": "Power", "track_width": POWER_WIDTH},
               {**DEFAULT_CLASS, "name": "Radio", "track_width": rf_width()}]
# Checks switched off on purpose: there is no silkscreen in a closed case, the stock courtyards
# ask for more rework room than the placer leaves (it keeps GAP between land patterns), and
# the stock footprints are copies in the project library.
IGNORED = ("courtyards_overlap", "silk_overlap", "silk_over_copper", "silk_edge_clearance", "text_height",
           "text_thickness", "lib_footprint_mismatch")


def turn(x, y, rot):
    """A point of a footprint after KiCad turns the footprint by rot degrees."""
    a = math.radians(rot)
    return x * math.cos(a) + y * math.sin(a), -x * math.sin(a) + y * math.cos(a)


def pad_positions(fp, x, y, rot, side="F"):
    out = {}
    for num, px, py, w, h in pads_of(fp):
        dx, dy = turn(px, py, rot)
        if side == "B":                    # KiCad turns the footprint, then flips it left to right
            dx = -dx
        out.setdefault(num, []).append((x + dx, y + dy))
    return out


def size(fp, rot):
    w, h = extent(fp)
    return (h, w) if rot % 180 else (w, h)


def unconnected_nets() -> dict[tuple[str, str], str]:
    """Names KiCad gave to the nets of no-connect pins, so the board can carry the same."""
    out = {}
    for net in ET.parse(ROOT / "electrical" / "out" / "netlist.xml").getroot().iter("net"):
        if net.get("name").startswith("unconnected-"):
            for node in net.iter("node"):
                out[(node.get("ref"), node.get("pin"))] = net.get("name")
    return out


def write_project():
    """Board rules live in the project file, next to the board."""
    path = ROOT / "electrical" / "kicad" / f"{PROJECT}.kicad_pro"
    pro = json.loads(path.read_text()) if path.exists() else {}
    pro.setdefault("meta", {"filename": path.name, "version": 3})
    settings = pro.setdefault("board", {}).setdefault("design_settings", {})
    settings.setdefault("rules", {}).update(RULES)
    settings.setdefault("rule_severities", {}).update({k: "ignore" for k in IGNORED})
    nets = pro.setdefault("net_settings", {})
    nets["classes"] = NET_CLASSES
    nets["netclass_patterns"] = ([{"netclass": "Power", "pattern": n} for n in POWER_NETS]
                                 + [{"netclass": "Radio", "pattern": n} for n in RF_NETS])
    path.write_text(json.dumps(pro, indent=2, sort_keys=True) + "\n")


def fixed_positions(comps, case):
    """Reference -> (x, y, side, rotation) for the parts the fit model places."""
    queues = {}
    for pl in placed_layout(case):
        if pl.part:
            queues.setdefault(pl.part, []).append(pl)
    out = {}
    for c in comps:
        body = S.body_of(c)
        if body in queues:
            pl = queues[body].pop(0)
            out[c.ref] = (*pl.centre, "B" if pl.face == "bottom" else "F", pl.rot)
    assert not any(queues.values()), {k: len(v) for k, v in queues.items() if v}
    return out


def place(comps, case):
    L, W = case.board
    placed = fixed_positions(comps, case)
    by_ref = {c.ref: c for c in comps}
    blocked = []                                   # rectangles nothing may be put on, top face
    for pl in placed_layout(case):
        if pl.part is None and pl.face in ("top", "both"):
            blocked.append((pl.x, pl.y, pl.x + pl.w, pl.y + pl.h))
    for ref, (x, y, side, rot) in placed.items():
        if side == "F":
            w, h = size(footprint_of(by_ref[ref]), rot)
            ml, mt, mr, mb = (max(f - GAP, 0.0) for f in FANOUT.get(by_ref[ref].value, (0, 0, 0, 0)))
            blocked.append((x - w / 2 - ml, y - h / 2 - mt, x + w / 2 + mr, y + h / 2 + mb))

    pads = {}                                      # net -> [(x, y, ref)] of placed pads
    claims = {}

    def register(c):
        x, y, side, rot = placed[c.ref]
        for num, points in pad_positions(footprint_of(c), x, y, rot, side).items():
            net = c.nets.get(num)
            if net:
                pads.setdefault(net, []).extend((px, py, c.ref) for px, py in points)

    for ref in placed:
        register(by_ref[ref])

    def free(x, y, w, h):
        box = S.Placed("", "x", "top", x - w / 2 - S.EDGE, y - h / 2 - S.EDGE, w + 2 * S.EDGE, h + 2 * S.EDGE)
        if not S.on_board(box, case):
            return False
        x0, y0, x1, y1 = x - w / 2 - GAP, y - h / 2 - GAP, x + w / 2 + GAP, y + h / 2 + GAP
        return not any(x0 < b[2] and b[0] < x1 and y0 < b[3] and b[1] < y1 for b in blocked)

    def targets(c):
        """For each pin worth pulling on, the pad it should end up next to."""
        out = {}
        for num, net in c.nets.items():
            if not net or net in GROUND or net not in pads:
                continue
            same = [q for q in pads[net] if by_ref[q[2]].sheet == c.sheet] or pads[net]
            chips = [q for q in same if len(by_ref[q[2]].sym.pins) > 2] or same
            out[num] = min(chips, key=lambda q: claims.get((net, q[:2]), 0))
        return out

    todo = [c for c in comps if c.ref not in placed and footprint_of(c)]
    while todo:
        ready = [(c, t) for c in todo for t in [targets(c)] if t]
        assert ready, f"nothing to hang these on: {[c.ref for c in todo]}"
        # First the parts on the nets that must be short, then the small decoupling capacitors,
        # then parts tied by two pins before parts tied by one.
        def urgency(ct):
            c, want = ct
            decoupling = c.sym.name == "C" and c.fields.get("Package") == "0201" and len(want) == 1
            return any(n in SHORTEST for n in c.nets.values()), decoupling, len(want)

        c, want = max(ready, key=urgency)
        fp = footprint_of(c)
        cx = sum(q[0] for q in want.values()) / len(want)
        cy = sum(q[1] for q in want.values()) / len(want)
        best = None
        n = int(REACH / STEP)
        for rot in (0, 90, 180, 270):
            w, h = size(fp, rot)
            local = {num: turn(px, py, rot) for num, px, py, _, _ in pads_of(fp)}
            for i in range(-n, n + 1):
                for j in range(-n, n + 1):
                    x, y = cx + i * STEP, cy + j * STEP
                    cost = sum(math.hypot(x + local[num][0] - q[0], y + local[num][1] - q[1]) for num, q in want.items())
                    if (best is None or cost < best[0]) and free(x, y, w, h):
                        best = (cost, x, y, rot)
        assert best, f"no room for {c.ref}"
        _, x, y, rot = best
        placed[c.ref] = (round(x, 3), round(y, 3), "F", rot)
        w, h = size(fp, rot)
        blocked.append((x - w / 2, y - h / 2, x + w / 2, y + h / 2))
        for num, q in want.items():
            claims[(c.nets[num], q[:2])] = claims.get((c.nets[num], q[:2]), 0) + 1
        register(c)
        todo.remove(c)
    return placed


def layout() -> dict:
    case = ENVELOPES[ADOPTED]
    comps = [c for c in build() if footprint_of(c)]
    placed = place(comps, case)
    L, W = case.board
    sheet = {name: uid("sheet", name) for name, _ in SHEETS}
    nc = unconnected_nets()
    parts = []
    for c in comps:
        x, y, side, rot = placed[c.ref]
        nets = {pin: net or nc[(c.ref, pin)] for pin, net in c.nets.items()}
        parts.append({"ref": c.ref, "value": c.value, "footprint": footprint_of(c), "x": round(x, 3), "y": round(y, 3),
                      "side": side, "rot": rot, "dnp": c.dnp, "path": f"/{sheet[c.sheet]}/{uid(c.sheet, c.ref)}",
                      "fields": {k: v for k, v in c.fields.items() if k not in ("Footprint", "Datasheet")},
                      "nets": nets})
    # The radio line's surroundings: the top pour stays out, so the line sees only the plane below.
    boxes = []
    for part in parts:
        if set(part["nets"].values()) & set(RF_NETS) and len(part["nets"]) <= 2:
            w, h = size(part["footprint"], part["rot"])
            boxes.append((part["x"] - w / 2, part["y"] - h / 2, part["x"] + w / 2, part["y"] + h / 2))
    soc = next(p for p in parts if p["value"] == "nRF54L15")
    ant_pin = pad_positions(soc["footprint"], soc["x"], soc["y"], soc["rot"])["31"][0]
    boxes.append((ant_pin[0] - 0.5, ant_pin[1] - 0.3, ant_pin[0], ant_pin[1] + 0.3))
    m = 0.3
    rf_region = [round(v, 3) for v in (min(b[0] for b in boxes) - m, min(b[1] for b in boxes) - m,
                                       max(b[2] for b in boxes) + m, max(b[3] for b in boxes) + m)]
    keepouts = [{"name": pl.name, "face": pl.face, "x": pl.x, "y": pl.y, "w": pl.w, "h": pl.h}
                for pl in placed_layout(case) if pl.part is None]
    return {"lib": LIB_NAME, "project": PROJECT, "length": round(L, 3), "width": round(W, 3),
            "outline": "ellipse", "thickness": case.board_t, "keepouts": keepouts,
            "rf_region": rf_region,
            "rules": RULES, "parts": parts}


if __name__ == "__main__":
    data = layout()
    write_project()
    out = ROOT / "electrical" / "out" / "board.json"
    out.write_text(json.dumps(data, indent=1) + "\n")
    print(f"{len(data['parts'])} footprints on an oval board {data['length']} x {data['width']} mm -> {out.name}")
