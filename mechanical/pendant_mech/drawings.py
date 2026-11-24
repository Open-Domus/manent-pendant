"""SVG drawings for the design document: the board seen from the front and a section along the case."""
import math

from . import stack as S
from .checks import envelope_report
from .params import ENVELOPES

INK, RIM, STONE, BOARD, PART, UNDER, CELL, KEEP = "#222", "#c9c5bd", "#b23a2e", "#3d7a4f", "#33475b", "#8fa3b5", "#c2603c", "#e8c66a"


def _svg(body, w, h, scale=22, left=1.0):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{-left:.2f} -1 {w + left + 1:.2f} {h + 2:.2f}" '
            f'width="{(w + left + 1) * scale:.0f}" font-family="sans-serif">\n'
            f'<rect x="{-left:.2f}" y="-1" width="{w + left + 1:.2f}" height="{h + 2:.2f}" fill="#fff"/>\n{body}</svg>\n')


def _rect(x, y, w, h, fill, dash=False, rx=0.0, opacity=1.0):
    d = ' stroke-dasharray="0.3 0.2"' if dash else ""
    return (f'<rect x="{x:.2f}" y="{y:.2f}" width="{w:.2f}" height="{h:.2f}" rx="{rx}" fill="{fill}" '
            f'fill-opacity="{opacity}" stroke="{INK}" stroke-width="0.05"{d}/>\n')


def _oval(cx, cy, length, width, fill, opacity=1.0):
    return (f'<ellipse cx="{cx:.2f}" cy="{cy:.2f}" rx="{length / 2:.2f}" ry="{width / 2:.2f}" fill="{fill}" '
            f'fill-opacity="{opacity}" stroke="{INK}" stroke-width="0.05"/>\n')


def _text(x, y, s, size=0.7):
    return f'<text x="{x:.2f}" y="{y:.2f}" font-size="{size}" fill="{INK}">{s}</text>\n'


def plan(key: str) -> str:
    """Seen from the front, through the stone, with the bail on the left.
    Solid: outer face of the board. Dashed: what hangs under it."""
    p, rep = ENVELOPES[key], envelope_report(key)
    off = p.wall + p.board_gap
    L, W = p.board
    cx, cy = p.length / 2, p.width / 2
    body = (f'<circle cx="-2.9" cy="{cy:.2f}" r="3.2" fill="none" stroke="{INK}" stroke-width="0.9" stroke-opacity="0.35"/>\n'
            + _oval(cx, cy, p.length, p.width, RIM) + _oval(cx, cy, p.cavity[0], p.cavity[1], "#fff")
            + _oval(cx, cy, L, W, BOARD, 0.35))
    if rep["cell"]:
        ln, wd, _ = rep["cell"]["size"]
        body += _rect(cx - ln / 2, cy - wd / 2, ln, wd, CELL, dash=True, opacity=0.25)
        body += _text(cx - ln / 2 + 0.4, cy + wd / 2 - 0.5, f"cell {rep['cell']['mpn']} (under the board)", 0.6)
    for pl in rep["placed"]:
        fill = KEEP if pl["part"] is None else (UNDER if pl["face"] == "bottom" else PART)
        body += _rect(off + pl["x"], off + pl["y"], pl["w"], pl["h"], fill, dash=pl["face"] == "bottom",
                      opacity=0.45 if pl["part"] is None else 0.9)
    for pl in rep["placed"]:
        if pl["part"] in ("soc", "pmic", "flash", "mic", "button", "led", "antenna"):
            body += _text(off + pl["x"], off + pl["y"] - 0.15, pl["name"], 0.55)
    return _svg(body, p.length, p.width, left=7.5)


def section(key: str) -> str:
    """Cut along the case. The chest is at the bottom, the bail on the left."""
    p, rep, parts = ENVELOPES[key], envelope_report(key), S.load_parts()
    off, H = p.wall + p.board_gap, p.height
    cl, _, ch = p.cavity
    up = lambda z, h: H - z - h                      # SVG y of a layer that starts z above the back
    body = _rect(0, up(0, p.rim_height), p.length, p.rim_height, RIM, rx=1.0)
    body += _rect(p.wall, up(p.back, ch), cl, ch, "#fff")
    # the stone: flat underneath, a dome on top
    y0, y1 = up(p.rim_height - p.stone_edge, 0), up(p.rim_height, 0)
    dome = " ".join(f"L{p.wall + cl / 2 * (1 + math.cos(math.radians(t))):.2f} "
                    f"{y1 - p.stone_rise * math.sin(math.radians(t)):.2f}" for t in range(0, 181, 6))
    body += (f'<path d="M{p.wall:.2f} {y0:.2f} L{p.wall + cl:.2f} {y0:.2f} {dome} Z" fill="{STONE}" fill-opacity="0.55" '
             f'stroke="{INK}" stroke-width="0.05"/>\n')
    board_z = p.back + rep["cell"]["board_to_back"] if rep["cell"] else H - p.stone - 2.0
    if rep["cell"]:
        ln, _, th = rep["cell"]["size"]
        x0 = (p.length - ln) / 2
        body += _rect(x0, up(p.back + S.CELL_PAD, th), ln, th, CELL, opacity=0.6)
        body += _text(x0 + 0.4, up(p.back + S.CELL_PAD, th) + th / 2 + 0.25, f"cell, {rep['cell']['capacity_mah']} mAh")
    body += _rect(off, up(board_z, p.board_t), p.board[0], p.board_t, BOARD)
    for pl in rep["placed"]:
        if pl["part"] is None:
            continue
        h = parts["parts"][pl["part"]]["size"][2]
        if pl["face"] == "top":
            body += _rect(off + pl["x"], up(board_z + p.board_t, h), pl["w"], h, PART)
        else:
            h = min(h, board_z - p.back)
            body += _rect(off + pl["x"], up(board_z - h, h), pl["w"], h, UNDER)
    return _svg(body, p.length, H)


if __name__ == "__main__":
    out = S.ROOT / "mechanical" / "out"
    out.mkdir(exist_ok=True)
    for key in ENVELOPES:
        (out / f"plan-{key}.svg").write_text(plan(key))
        (out / f"section-{key}.svg").write_text(section(key))
    print(f"drawings written to {out}")
