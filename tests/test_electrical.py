from pathlib import Path

import pytest

from gen import checks
from gen.design import build, netlist

NETLIST = Path(__file__).resolve().parents[1] / "electrical" / "out" / "netlist.xml"


def test_circuit_rules_hold():
    assert checks.lint() == []


def test_kicad_reads_the_same_nets_we_wrote():
    if not NETLIST.exists():
        pytest.skip("run `make schematic` first")
    assert checks.compare(NETLIST) == []
    assert len(checks.kicad_netlist(NETLIST)) == len(netlist()) > 40


def test_light_follows_the_microphone_rail():
    # The steady glow must not depend on firmware: its switch is gated by VMIC itself.
    comps = build()
    gate = [c for c in comps if c.sym.name == "NMOS" and c.nets["1"] == "VMIC"]
    assert len(gate) == 1 and gate[0].nets["3"] == "LED_SW"
    assert all("VMIC" in c.nets.values() for c in comps if c.value == "T5838")


def test_firmware_can_add_light_but_not_remove_it():
    comps = build()
    led = next(c for c in comps if c.sym.name == "LED")
    cathode = led.nets["1"]
    paths = {next(n for n in c.nets.values() if n != cathode) for c in comps
             if c.sym.name == "R" and cathode in c.nets.values()}
    assert paths == {"LED_SW", "LED_HI"}
    # Nothing but the light and its two resistors touches the cathode: no pin can hold it off.
    assert len(netlist(comps)[cathode]) == 3


def test_muting_cuts_both_microphones_with_one_switch():
    comps = build()
    pmic = next(c for c in comps if c.value == "nPM1304")
    names = {p.name: pmic.nets[p.number] for p in pmic.sym.pins}
    assert names["LSOUT1"] == "VMIC" and names["GPIO1"] == "MIC_EN"
    assert len([c for c in comps if c.value == "T5838"]) == 2


def test_both_nordic_chips_are_the_qfn_versions():
    fps = {c.value: c.fields["Footprint"] for c in build() if c.value in ("nRF54L15", "nPM1304")}
    assert "QFN-48" in fps["nRF54L15"] and "QFN-32" in fps["nPM1304"]


def test_board_is_complete_and_breaks_no_rule():
    import json
    drc = NETLIST.with_name("drc.json")
    if not drc.exists():
        pytest.skip("run `make board` first")
    report = json.loads(drc.read_text())
    assert report["violations"] == []
    assert report["schematic_parity"] == []       # same parts, footprints and nets as the schematic
    # The tracks are in electrical/kicad/pendant.ses. If the placement changed since they were
    # drawn, connections open up here: run `make route` again.
    assert report["unconnected_items"] == []


def test_kicad_put_every_pad_where_the_placer_assumed():
    import json
    board, pads = NETLIST.with_name("board.json"), NETLIST.with_name("pads.json")
    if not (board.exists() and pads.exists()):
        pytest.skip("run `make board` first")
    from gen.board import pad_positions
    real = {}
    for ref, num, x, y, net in json.loads(pads.read_text()):
        real.setdefault((ref, num), []).append((x, y, net))
    checked = 0
    for part in json.loads(board.read_text())["parts"]:
        for num, points in pad_positions(part["footprint"], part["x"], part["y"], part["rot"], part["side"]).items():
            for x, y in points:
                assert min(abs(x - a) + abs(y - b) for a, b, _ in real[(part["ref"], num)]) < 0.01, (part["ref"], num)
                checked += 1
            assert all(net == part["nets"][num] for _, _, net in real[(part["ref"], num)]), (part["ref"], num)
    assert checked > 200


def test_placed_parts_stay_close_to_what_they_connect_to():
    import json
    path = NETLIST.with_name("board.json")
    if not path.exists():
        pytest.skip("run `make board` first")
    from gen.board import pad_positions
    data = json.loads(path.read_text())
    pads = {}
    for part in data["parts"]:
        for num, points in pad_positions(part["footprint"], part["x"], part["y"], part["rot"], part["side"]).items():
            pads.setdefault(part["nets"].get(num), []).extend((x, y, part["ref"]) for x, y in points)
    # Every decoupling capacitor of the microcontroller within 3 mm of a supply pin of it.
    soc = next(p["ref"] for p in data["parts"] if p["value"] == "nRF54L15")
    caps = [p["ref"] for p in data["parts"] if p["value"] == "100nF" and "/" + p["path"].split("/")[1] ==
            "/" + next(q for q in data["parts"] if q["ref"] == soc)["path"].split("/")[1]]
    assert len(caps) == 4
    vdd = [(x, y) for x, y, ref in pads["V1V8"] if ref == soc]
    for cap in caps:
        own = [(x, y) for x, y, ref in pads["V1V8"] if ref == cap]
        assert min(((x - a) ** 2 + (y - b) ** 2) ** 0.5 for x, y in own for a, b in vdd) < 3.0, cap


def test_no_vibration_motor():
    assert not any("haptic" in c.value.lower() or "motor" in c.value.lower() for c in build())


def _tracks():
    import json
    path = NETLIST.with_name("tracks.json")
    if not path.exists():
        pytest.skip("run `make board` first")
    return json.loads(path.read_text())


def _share_at_width(nets, width):
    rows = [r for r in _tracks() if r[0] in nets]
    total = sum(r[3] for r in rows)
    assert total > 0
    return sum(r[3] for r in rows if r[2] >= width - 1e-6) / total


def test_radio_line_width_is_fifty_ohms_on_the_assumed_stack():
    from gen.board import STACK, microstrip_ohms, rf_width
    assert 0.15 < rf_width() < 0.25
    assert microstrip_ohms(rf_width(), STACK["prepreg_mm"], STACK["er"]) == pytest.approx(50, abs=1.5)


def test_no_signal_runs_on_the_ground_layer():
    assert [r[0] for r in _tracks() if r[1] == "In1.Cu"] == []


def test_radio_line_is_drawn_at_its_width():
    from gen.board import RF_NETS, rf_width
    assert _share_at_width(RF_NETS, rf_width()) > 0.9


def test_supply_tracks_are_wide():
    from gen.board import POWER_NETS, POWER_WIDTH
    assert _share_at_width(POWER_NETS, POWER_WIDTH) > 0.9


@pytest.mark.parametrize("pins, footprint", [
    ("nrf54l15_qfn48", "QFN-48-1EP_6x6mm_P0.4mm_EP4.6x4.6mm"),
    ("npm1304_qfn32", "QFN-32-1EP_5x5mm_P0.5mm_EP3.45x3.45mm"),
])
def test_qfn_land_pattern_fits_the_package_nordic_draws(pins, footprint):
    # Nordic prints the package, not the land pattern, so this checks that the stock pattern
    # suits the package: every lead lands on its pad at any tolerance, with solder beyond the
    # body edge, and the centre land is within the range of the exposed pad.
    import yaml
    from gen import footprints
    root = Path(__file__).resolve().parents[1]
    pkg = yaml.safe_load((root / "parts" / "pins" / f"{pins}.yaml").read_text())["package"]
    lim = pkg["limits"]
    pads = footprints.pads_of(footprint)
    centre = max(pads, key=lambda p: p[3] * p[4])
    leads = [p for p in pads if p is not centre]
    left = sorted((p for p in leads if p[1] == min(q[1] for q in leads)), key=lambda p: p[2])
    assert len(leads) == 4 * len(left)
    steps = {round(b[2] - a[2], 4) for a, b in zip(left, left[1:])}
    assert steps == {pkg["pitch"]}
    _, x, _, length, width = left[0]
    inner, outer = abs(x) - length / 2, abs(x) + length / 2
    assert lim["lead_width"][0] <= width <= lim["lead_width"][2]
    assert pkg["pitch"] - width >= 0.2                         # room for solder mask between pads
    assert inner <= lim["body"][1] / 2 - lim["lead_length"][2] + 1e-6   # the longest lead is covered
    assert outer - lim["body"][2] / 2 >= 0.2                   # a fillet outside the largest body
    assert lim["exposed_pad"][0] <= centre[3] <= lim["exposed_pad"][2]
    assert centre[3] == centre[4]
    assert inner - centre[3] / 2 >= 0.2                        # leads clear of the centre land
