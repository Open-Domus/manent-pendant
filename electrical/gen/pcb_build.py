"""Build electrical/kicad/pendant.kicad_pcb from electrical/out/board.json.

Runs with KiCad's own Python (the pcbnew module), not the project environment:
    python3 gen/pcb_build.py          (from the electrical directory)
Footprints are placed and their pads given their nets, and the ground plane of the first inner
layer is outlined. No tracks are drawn, so the plane is left unpoured: nothing reaches it yet.
"""
import json
import math
from pathlib import Path

import pcbnew

HERE = Path(__file__).resolve().parents[1]
data = json.loads((HERE / "out" / "board.json").read_text())
lib = str(HERE / "kicad" / (data["lib"] + ".pretty"))
mm = pcbnew.FromMM
pt = lambda x, y: pcbnew.VECTOR2I(mm(x), mm(y))
L, W = data["length"], data["width"]

board = pcbnew.BOARD()
board.SetCopperLayerCount(4)
board.GetDesignSettings().SetBoardThickness(mm(data["thickness"]))
nets = {}
for part in data["parts"]:
    for name in part["nets"].values():
        if name not in nets:
            nets[name] = pcbnew.NETINFO_ITEM(board, name)
            board.Add(nets[name])

for part in data["parts"]:
    fp = pcbnew.FootprintLoad(lib, part["footprint"])
    assert fp is not None, part["footprint"]
    fp.SetFPID(pcbnew.LIB_ID(data["lib"], part["footprint"]))
    fp.SetReference(part["ref"])
    fp.SetValue(part["value"])
    fp.SetPath(pcbnew.KIID_PATH(part["path"]))
    fp.SetDNP(part["dnp"])
    for key, value in part["fields"].items():
        fp.SetField(key, value)
        fp.GetField(key).SetVisible(False)
    board.Add(fp)
    fp.SetPosition(pt(part["x"], part["y"]))
    fp.SetOrientationDegrees(part["rot"])
    if part["side"] == "B":
        fp.Flip(fp.GetPosition(), pcbnew.FLIP_DIRECTION_LEFT_RIGHT)
    for pad in fp.Pads():
        net = part["nets"].get(pad.GetNumber())
        if net:
            pad.SetNet(nets[net])


def outline_points(inset=0.0, steps=144):
    """The ellipse of the board, moved inwards by inset, starting at the tip away from the bail
    and running through the edge with the switch, the tip with the bail and the antenna edge."""
    a, b = L / 2 - inset, W / 2 - inset
    return [(L / 2 + a * math.cos(2 * math.pi * i / steps), W / 2 + b * math.sin(2 * math.pi * i / steps))
            for i in range(steps)]


def edge_y(x, inset):
    """Where the ellipse, moved inwards by inset, crosses x on the antenna side."""
    a, b = L / 2 - inset, W / 2 - inset
    return W / 2 - b * math.sqrt(1 - ((x - L / 2) / a) ** 2)


def line(a, b, layer, width=0.05):
    s = pcbnew.PCB_SHAPE(board, pcbnew.SHAPE_T_SEGMENT)
    s.SetStart(pt(*a)), s.SetEnd(pt(*b)), s.SetLayer(layer), s.SetWidth(mm(width))
    board.Add(s)


def note(text, x, y, layer, size=0.5):
    t = pcbnew.PCB_TEXT(board)
    t.SetText(text), t.SetPosition(pt(x, y)), t.SetLayer(layer)
    t.SetTextSize(pcbnew.VECTOR2I(mm(size), mm(size))), t.SetTextThickness(mm(size / 6))
    board.Add(t)


def ground_plane(points):
    """Ground on the first inner layer."""
    z = pcbnew.ZONE(board)
    z.SetZoneName("ground plane")
    o = z.Outline()
    o.NewOutline()
    for x, y in points:
        o.Append(mm(x), mm(y))
    z.SetLayer(pcbnew.In1_Cu)
    z.SetNet(nets["GND"])
    z.SetPadConnection(pcbnew.ZONE_CONNECTION_FULL)
    z.SetMinThickness(mm(0.1))
    z.SetLocalClearance(mm(0.15))
    z.SetIslandRemovalMode(pcbnew.ISLAND_REMOVAL_MODE_ALWAYS)
    board.Add(z)


edge = outline_points()
for a, b in zip(edge, edge[1:] + edge[:1]):
    line(a, b, pcbnew.Edge_Cuts)
plane = outline_points(0.3)
for k in data["keepouts"]:
    x0, y0, x1, y1 = k["x"], k["y"], k["x"] + k["w"], k["y"] + k["h"]
    corners = [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
    for a, b in zip(corners, corners[1:] + corners[:1]):
        line(a, b, pcbnew.Dwgs_User, 0.03)
    note(k["name"], (x0 + x1) / 2, y0 - 0.35, pcbnew.Cmts_User, 0.3)
    if k["name"].startswith("antenna"):
        # No ground under the antenna: the plane's outline steps around that stretch of the edge.
        # A notch, not a hole or a rule area: the autorouter reads a rule area as "no tracks" and
        # does not see holes.
        assert y0 == 0.0 and y1 > edge_y(x0, 0.3) and y1 > edge_y(x1, 0.3)
        notch = [(x0, edge_y(x0, 0.3)), (x0, y1), (x1, y1), (x1, edge_y(x1, 0.3))]
        cut = [i for i, q in enumerate(plane) if x0 <= q[0] <= x1 and q[1] < y1]
        assert cut == list(range(cut[0], cut[-1] + 1))
        plane = plane[:cut[0]] + notch + plane[cut[-1] + 1:]
note("Top copper faces the stone, bottom copper faces the cell. In1: ground. In2: signals.",
     L / 2, -1.2, pcbnew.Cmts_User, 0.5)
ground_plane(plane)

out = HERE / "kicad" / (data["project"] + ".kicad_pcb")
pcbnew.SaveBoard(str(out), board)
# Where KiCad really put every pad, for the test that compares it with what the placer assumed.
pads = [[fp.GetReference(), pad.GetNumber(), pcbnew.ToMM(pad.GetPosition().x), pcbnew.ToMM(pad.GetPosition().y),
         pad.GetNetname()] for fp in board.GetFootprints() for pad in fp.Pads() if pad.GetNumber()]
(HERE / "out" / "pads.json").write_text(json.dumps(pads) + "\n")
print(f"{len(data['parts'])} footprints, {len(nets)} nets -> {out.name}")
