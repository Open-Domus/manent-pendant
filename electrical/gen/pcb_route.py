"""Hand the placed board to an autorouter and bring the tracks back.

Runs with KiCad's own Python:   python3 gen/pcb_route.py export | import <session file>
`export` writes out/pendant.dsn; Freerouting turns it into a session file; `import` reads that
into the board, adds ground pours on both outer layers, fills them and saves.
"""
import json
import sys
from pathlib import Path

import pcbnew

HERE = Path(__file__).resolve().parents[1]
pcb = str(HERE / "kicad" / "pendant.kicad_pcb")
board = pcbnew.LoadBoard(pcb)
if sys.argv[1] == "export":
    dsn = HERE / "out" / "pendant.dsn"
    assert pcbnew.ExportSpecctraDSN(board, str(dsn))
    text = dsn.read_text()
    assert "(clearance 90)" in text
    text = text.replace("(clearance 90)", "(clearance 100)")            # route at 0.1, check at 0.09
    dsn.write_text(text)
    # The first inner layer is the ground plane: the router's rules file switches it off for
    # tracks. (Declaring the layer as a power layer in the board description stops the router
    # from reaching the plane at all.)
    layer = lambda name, active, way: (
        f"    (layer_rule {name}\n      (active {active})\n      (preferred_direction {way})\n"
        "      (preferred_direction_trace_costs 1.0)\n      (against_preferred_direction_trace_costs 2.0)\n    )\n")
    (HERE / "out" / "pendant.rules").write_text(
        "(rules PCB pendant\n  (snap_angle fortyfive_degree)\n  (autoroute_settings\n    (fanout off)\n"
        "    (autoroute on)\n    (postroute on)\n    (vias on)\n    (via_costs 50)\n    (plane_via_costs 5)\n"
        "    (start_ripup_costs 100)\n    (start_pass_no 1)\n"
        + layer("F.Cu", "on", "horizontal") + layer("In1.Cu", "off", "vertical")
        + layer("In2.Cu", "on", "vertical") + layer("B.Cu", "on", "horizontal") + "  )\n)\n")
    print("out/pendant.dsn written")
else:
    assert pcbnew.ImportSpecctraSES(board, str(HERE / sys.argv[2]))
    narrow = 0
    for t in board.GetTracks():             # the router necks some tracks down below the board's minimum
        if t.Type() != pcbnew.PCB_VIA_T and t.GetWidth() < pcbnew.FromMM(0.09):
            t.SetWidth(pcbnew.FromMM(0.09))
            narrow += 1
    print(f"{narrow} segments widened to 0.09 mm")
    # No poured copper next to the radio line on the top layer: only the plane under it.
    data = json.loads((HERE / "out" / "board.json").read_text())
    x0, y0, x1, y1 = (pcbnew.FromMM(v) for v in data["rf_region"])
    if not any(z.GetZoneName() == "radio line: no top pour" for z in board.Zones()):
        area = pcbnew.ZONE(board)
        area.SetZoneName("radio line: no top pour")
        shape = area.Outline()
        shape.NewOutline()
        for x, y in ((x0, y0), (x1, y0), (x1, y1), (x0, y1)):
            shape.Append(x, y)
        area.SetIsRuleArea(True)
        area.SetLayer(pcbnew.F_Cu)
        area.SetDoNotAllowZoneFills(True)
        area.SetDoNotAllowTracks(False), area.SetDoNotAllowVias(False), area.SetDoNotAllowPads(False)
        area.SetDoNotAllowFootprints(False)
        board.Add(area)
    # Ground pours on both outer layers, around the tracks: the router counts on the inner plane
    # to join every ground pad, and leaves a few ground tracks that never reach it.
    plane = next(z for z in board.Zones() if z.GetZoneName() == "ground plane")
    chain = plane.Outline().Outline(0)
    have = {z.GetLayer() for z in board.Zones() if not z.GetIsRuleArea()}
    for layer, name in ((pcbnew.F_Cu, "ground pour, top"), (pcbnew.B_Cu, "ground pour, bottom")):
        if layer in have:
            continue
        pour = pcbnew.ZONE(board)
        shape = pour.Outline()
        shape.NewOutline()
        for i in range(chain.PointCount()):
            shape.Append(chain.CPoint(i).x, chain.CPoint(i).y)
        pour.SetLayer(layer)
        pour.SetNetCode(plane.GetNetCode())
        pour.SetZoneName(name)
        pour.SetPadConnection(pcbnew.ZONE_CONNECTION_FULL)
        pour.SetMinThickness(pcbnew.FromMM(0.1))
        pour.SetLocalClearance(pcbnew.FromMM(0.15))
        pour.SetIslandRemovalMode(pcbnew.ISLAND_REMOVAL_MODE_ALWAYS)
        board.Add(pour)
    pcbnew.ZONE_FILLER(board).Fill(board.Zones())
    pcbnew.SaveBoard(pcb, board)
    tracks = board.GetTracks()
    vias = sum(1 for t in tracks if t.Type() == pcbnew.PCB_VIA_T)
    # Every track segment, for the tests: net, layer, width, length, ends.
    rows = [[t.GetNetname(), t.GetLayerName(), pcbnew.ToMM(t.GetWidth()), round(pcbnew.ToMM(t.GetLength()), 4),
             pcbnew.ToMM(t.GetStart().x), pcbnew.ToMM(t.GetStart().y), pcbnew.ToMM(t.GetEnd().x), pcbnew.ToMM(t.GetEnd().y)]
            for t in tracks if t.Type() != pcbnew.PCB_VIA_T]
    (HERE / "out" / "tracks.json").write_text(json.dumps(rows) + "\n")
    print(f"{len(tracks) - vias} track segments, {vias} vias -> pendant.kicad_pcb")
