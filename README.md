# Manent pendant: hardware

Hardware design of the Manent pendant: a jewel on a chain that listens for speech around
its wearer, records it, and hands it to the phone over Bluetooth LE. An oval cabochon of
coloured glass in a titanium rim, 40 x 26 mm, whose stone glows while it listens. The stone
and its light come in red, green or blue, chosen at order.
It is the band of `manent-band` in another form: the same circuit, net for net, in a case
made to be looked at. Firmware and radio protocol live in the `mnemo-band` repository.

Public page: [manentlabs.it/en/pendant/](https://manentlabs.it/en/pendant/) (English), [manentlabs.it/pendente/](https://manentlabs.it/pendente/) (Italian).

Nothing here has been built or measured. This is a first design on paper, checked by
scripts, and several of its choices still wait for the project owner.

| What | Where |
| --- | --- |
| Design document: the jewel, requirements, decisions | [docs/design.md](docs/design.md) |
| Does it fit? Case, layers, cell, board area | [docs/space-budget.md](docs/space-budget.md) |
| How long does it last? | [docs/power-budget.md](docs/power-budget.md) |
| What is undecided or unknown, and what would settle it | [docs/open-questions.md](docs/open-questions.md) |
| Parts with sizes and how far each is verified | [parts/parts.yaml](parts/parts.yaml) |
| Circuit, as data | [electrical/gen/design.py](electrical/gen/design.py) |
| Schematic (KiCad 10), PDF, bill of materials | `electrical/kicad/`, `electrical/out/` |
| Board: an ellipse, placed and routed by scripts, not reviewed | `electrical/kicad/pendant.kicad_pcb`, `electrical/out/board-*.svg` |
| Fit model, drawings, STEP | `mechanical/`, `mechanical/out/` |

## Build

Needs `uv`, and either KiCad 10 or Docker (`docker pull kicad/kicad:10.0`).

```
make all        # schematic, board, checks, tests, fit report, drawings, budgets, STEP
make test       # tests only
make route      # draw the tracks again with Freerouting (needs Java and its jar; see tools/route.sh)
```

The schematic and the board are generated: edit `electrical/gen/design.py` and the fit
model, never the `.kicad_sch` or `.kicad_pcb` files.
Every pin carries a label with its net name instead of drawn wires. `make schematic` runs
KiCad's rule check and compares the netlist KiCad reads with the one in `design.py`.

The board is placed and routed by scripts and passes KiCad's checks, but nobody has reviewed
it: see "Board" in the design document before taking it for more than it is. The tracks
are kept in `electrical/kicad/pendant.ses`; when the placement changes, `make route` draws
them again.

## What it shares with the band

The circuit (`electrical/gen/design.py` differs from the band's only in the switch and in
its notes), the pin tables in `parts/pins`, the checks, the power budget's inputs and the
build scripts. A change to the circuit belongs in both repositories.

## Licences

As for the ring and the band: hardware under CERN-OHL-S v2 (`LICENSE`), documents under
CC BY-SA 4.0 (`LICENSE-docs`). The licence of the scripts is not decided.
