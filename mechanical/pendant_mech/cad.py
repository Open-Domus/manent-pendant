"""Solid model of the pendant for STEP export and a visual check. Run as a module.

The shapes are the fit model's, not a design for manufacture: the rim is a plain oval tube,
the stone a slice of an ellipsoid on a flat rim, the bail a ring. Sound holes, the pusher,
the seat of the stone and the joint of the back cover are not drawn."""
from build123d import Box, Compound, Ellipse, Pos, Rot, Sphere, Torus, export_step, extrude, scale

from . import stack as S
from .checks import envelope_report
from .params import ENVELOPES

BAIL = (3.2, 0.9)       # the ring the chain runs through: radius of its centre line, radius of its wire


def _box(x, y, z, w, h, t, label):
    """Box with its low corner at (x, y, z); origin at a corner of the box around the case, on the back."""
    b = Pos(x + w / 2, y + h / 2, z + t / 2) * Box(w, h, t)
    b.label = label
    return b


def _oval(p, length, width, z, t, label):
    """An elliptical plate, centred on the case, from z to z + t."""
    s = Pos(p.length / 2, p.width / 2, z) * extrude(Ellipse(length / 2, width / 2), t)
    s.label = label
    return s


def build(key: str) -> Compound:
    p, rep, parts = ENVELOPES[key], envelope_report(key), S.load_parts()
    cl, cw, ch = p.cavity
    rim = _oval(p, p.length, p.width, 0, p.rim_height, "rim") - _oval(p, cl, cw, 0, p.rim_height, "")
    rim.label = "rim"
    bail = Pos(-BAIL[0] + 0.3, p.width / 2, p.rim_height / 2) * Rot(90, 0, 0) * Torus(*BAIL)
    bail.label = "bail"
    back = _oval(p, cl, cw, 0, p.back, "back cover")
    stone = _oval(p, cl, cw, p.rim_height - p.stone_edge, p.stone_edge, "stone")
    dome = scale(Sphere(1.0) & (Pos(0, 0, 0.5) * Box(2, 2, 1)), by=(cl / 2, cw / 2, p.stone_rise))
    dome = Pos(p.length / 2, p.width / 2, p.rim_height) * dome
    dome.label = "stone, dome"
    solids = [rim, bail, back, stone, dome]
    off = p.wall + p.board_gap
    board_z = p.back + rep["cell"]["board_to_back"]
    L, W = p.board
    ln, wd, th = rep["cell"]["size"]
    solids.append(_box((p.length - ln) / 2, (p.width - wd) / 2, p.back + S.CELL_PAD, ln, wd, th,
                       f"cell {rep['cell']['mpn']}"))
    solids.append(_oval(p, L, W, board_z, p.board_t, "board"))
    for pl in rep["placed"]:
        if pl["part"] is None:
            continue
        h = parts["parts"][pl["part"]]["size"][2]
        if pl["face"] == "top":
            z = board_z + p.board_t
        else:
            h = min(h, board_z - p.back)
            z = board_z - h
        solids.append(_box(off + pl["x"], off + pl["y"], z, pl["w"], pl["h"], h, pl["name"]))
    return Compound(label=f"manent-pendant-{key}", children=solids)


if __name__ == "__main__":
    out = S.ROOT / "mechanical" / "out"
    out.mkdir(exist_ok=True)
    for key in ENVELOPES:
        model = build(key)
        export_step(model, str(out / f"pendant-{key}.step"))
        print(f"pendant-{key}.step: {len(model.children)} bodies, "
              f"bounding box {tuple(round(v, 2) for v in model.bounding_box().size)}")
