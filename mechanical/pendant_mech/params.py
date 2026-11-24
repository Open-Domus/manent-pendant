"""Case envelope parameters. All lengths in millimetres.

The pendant is an oval case that hangs from a chain: a metal rim, a flat back and a domed
stone in front, set as a cabochon. X runs along its length from the end with the bail,
Y across it, Z from the back, which lies on the chest, to the top of the stone.
The outline, the cavity and the board are all ellipses with the same centre.
"""
from dataclasses import dataclass, replace


@dataclass(frozen=True)
class CaseParams:
    name: str
    length: float
    width: float
    height: float            # at the centre, where the stone is thickest
    wall: float = 1.0        # the rim
    back: float = 0.8        # the cover on the chest side, with the charging pads
    stone_edge: float = 0.8  # the stone where the rim holds it
    stone_rise: float = 1.2  # how much thicker the stone is at its centre: the dome
    board_gap: float = 0.3   # between the board edge and the rim
    board_t: float = 0.6

    @property
    def board(self) -> tuple[float, float]:
        """Both axes of the board's ellipse."""
        m = 2 * (self.wall + self.board_gap)
        return self.length - m, self.width - m

    @property
    def stone(self) -> float:
        """Thickness of the stone at the centre."""
        return self.stone_edge + self.stone_rise

    @property
    def rim_height(self) -> float:
        return self.height - self.stone_rise

    @property
    def cavity(self) -> tuple[float, float, float]:
        """Both axes of the cavity's ellipse and its height under the flat underside of the stone."""
        return self.length - 2 * self.wall, self.width - 2 * self.wall, self.height - self.back - self.stone

    def resized(self, **kw) -> "CaseParams":
        return replace(self, **kw)


# Envelope A: the smallest oval the model accepts around the cell the band uses.
OVAL = CaseParams("A-oval", 40.0, 26.0, 9.5)
# Envelope B: the proportions of a cameo, for a wider cell.
CAMEO = CaseParams("B-cameo", 42.0, 31.0, 9.5)

ENVELOPES = {"A": OVAL, "B": CAMEO}
ADOPTED = "A"
