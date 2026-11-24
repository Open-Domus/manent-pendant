import pytest

from pendant_mech import stack as S
from pendant_mech.checks import SWEEP_HEIGHTS, SWEEP_WIDTHS, circuit_bodies, envelope_report, placed_layout, size_sweep
from pendant_mech.params import ADOPTED, ENVELOPES


@pytest.fixture(scope="module")
def reports():
    return {k: envelope_report(k) for k in ENVELOPES}


def test_both_envelopes_fit(reports):
    for key, rep in reports.items():
        assert rep["ok"], (key, rep["problems"])


def test_adopted_envelope_is_the_oval(reports):
    assert reports[ADOPTED]["case"] == [40.0, 26.0, 9.5]
    assert reports[ADOPTED]["cell"]["capacity_mah"] >= 100


def test_the_stack_adds_up_to_the_height_at_the_centre(reports):
    for key, rep in reports.items():
        assert sum(rep["stack"].values()) == pytest.approx(ENVELOPES[key].height, abs=0.02)


def test_a_case_too_thin_has_no_cell():
    thin = ENVELOPES["A"].resized(height=7.5)
    rep = envelope_report("A", thin)
    assert not rep["ok"] and rep["cell"] is None


def test_the_cell_clears_the_oval_rim(reports):
    for key, rep in reports.items():
        ln, wd, _ = rep["cell"]["size"]
        assert S.cell_in_cavity(ENVELOPES[key], ln, wd)
    # a cell as long as the cavity is wide open in the box, and still does not go into an oval
    p = ENVELOPES["A"]
    assert not S.cell_in_cavity(p, p.cavity[0] - 1.0, 15.0)


def test_every_placed_part_is_inside_the_ellipse_of_the_board():
    for p in ENVELOPES.values():
        for pl in placed_layout(p):
            if pl.part:
                assert S.on_board(pl, p), pl.name
    L, W = ENVELOPES["A"].board
    corner = S.Placed("in the corner of the box", "testpad", "top", 0.0, 0.0, 1.0, 1.0)
    assert not S.on_board(corner, ENVELOPES["A"])
    assert S.in_ellipse(L / 2, W / 2, L, W) and not S.in_ellipse(0.5, 0.5, L, W)


def test_microphones_are_at_the_two_tips(reports):
    for key, rep in reports.items():
        assert rep["mic_distance"] >= S.MIN_MIC_DISTANCE
        mics = [pl for pl in rep["placed"] if pl["part"] == "mic"]
        L, W = ENVELOPES[key].board
        assert all(pl["y"] + pl["h"] / 2 == pytest.approx(W / 2) for pl in mics)
        assert min(pl["x"] for pl in mics) < 2.0 and max(pl["x"] + pl["w"] for pl in mics) > L - 2.0


def test_switch_and_contacts_share_the_side_the_cell_leaves_free(reports):
    for key, rep in reports.items():
        _, W = ENVELOPES[key].board
        edge_of_cell = W / 2 + rep["cell"]["size"][1] / 2
        side = [pl for pl in rep["placed"] if pl["part"] in ("button", "contact")]
        assert len(side) == 5 and all(pl["face"] == "bottom" and pl["y"] > edge_of_cell for pl in side)


def test_every_part_of_the_circuit_is_in_the_model(reports):
    bodies = circuit_bodies()
    large = sorted(b for b in bodies if b not in S.SMALL)
    placed = sorted(pl["part"] for pl in reports[ADOPTED]["placed"] if pl["part"])
    assert placed == large and len(large) >= 19
    assert reports[ADOPTED]["area"]["small_parts"] == len(bodies) - len(large) > 40


def test_wider_or_taller_cases_never_lose_capacity():
    rows = size_sweep()
    assert all(r["capacity_mah"] for r in rows)
    by = {(r["case"][1], r["case"][2]): r["capacity_mah"] for r in rows}
    for i, w in enumerate(SWEEP_WIDTHS):
        for j, h in enumerate(SWEEP_HEIGHTS):
            if i:
                assert by[(w, h)] >= by[(SWEEP_WIDTHS[i - 1], h)]
            if j:
                assert by[(w, h)] >= by[(w, SWEEP_HEIGHTS[j - 1])]


def test_it_weighs_what_a_pendant_may(reports):
    assert reports[ADOPTED]["mass"]["total_g_estimate"] < 15


def test_parts_are_complete():
    parts = S.load_parts()
    for group in ("parts", "cells"):
        for key, part in parts[group].items():
            assert part["mpn"] and part["manufacturer"], key
            assert len(part["size"]) == 3 and all(v > 0 for v in part["size"]), key
            assert part["status"] in {"verified", "secondary", "unverified"}, key
    assert set(circuit_bodies()) - {"testpad"} <= set(parts["parts"])
