# Manent pendant: design

Status: first draft on paper, written 2026-11-24. No board, no case, no measurement.
Numbers are either from manufacturers' documents or estimates, and each table says which.
Choices marked "draft" were made to have something to check; the project owner has not
confirmed them. They are listed again in [open-questions.md](open-questions.md).

## What the pendant does

What the band does: it waits for sound, records when somebody speaks near its wearer, and
hands the audio to the phone, which turns it into text. It keeps a recording only until the
phone confirms it has it. A light shows that it is listening and one button mutes it.

It differs from the band in where it is worn and in what it has to be. It hangs on the
chest, a hand's width from the wearer's mouth and facing whoever they talk to, which is a
better place for a microphone than a wrist. And it is worn as a jewel, in plain sight, so
it has to be one: an object somebody would wear with nothing inside it.

The circuit is the band's, net for net, so that one firmware runs on both. This document
describes what is different: the case, the board that fits it, and the questions an oval of
metal and glass raises.

## The jewel

An oval cabochon in a bezel setting, the oldest way to set a stone, hung by a bail from a
chain.

- **The stone** is the front: a low cabochon of coloured glass, flat underneath and domed
  on top, 0.8 mm at its edge and 2 mm at its centre. Its underside is frosted, so the
  board does not show through. It comes in three colours, red, green and blue, chosen by
  whoever orders it: see "Colours".
- **The light is the stone.** The one light of the circuit sits at the exact centre of
  the board, under the middle of the stone. Off,
  the stone is dark. While the microphones have power it glows from inside, like an
  ember; while sound is being recorded it is lit. The requirement that other people can see
  when it listens becomes the thing people look at. The light has the colour of the stone,
  because coloured glass passes its own colour and little else.
- **The rim** is one oval band of polished titanium, 1 mm thick and 8.3 mm high, closed
  over the edge of the stone. Titanium is the ring's metal and it is light and kind to
  skin; a jeweller could make the same rim in silver or gold.
- **The back** is a flat cover of the resin the ring uses inside, lying on the chest. It
  carries four small gold pads in a row along one side and nothing else.
- **The bail** is a fixed loop at one tip, part of the rim, wide enough for a chain with
  its clasp. It is fixed, not hinged, so that the pendant does not turn over and show its
  back: a pendant face down hides its light.
- **Nothing else shows.** No socket and no seam on the front. The button is a pusher
  flush with the rim, on one long side, pressed by pinching the pendant between thumb and
  finger. The two sound holes are in the rim at the two tips, 0.8 mm each: one beside the
  bail, facing up towards the wearer's mouth, one at the bottom.

| | Envelope A (adopted, draft) | Envelope B |
| --- | --- | --- |
| Outline | oval, 40 x 26 mm | oval, 42 x 31 mm, the proportions of a cameo |
| Height | 9.5 mm at the centre of the stone, 8.3 at the rim | the same |
| Cell | about 120 mAh | about 160 mAh |
| Mass without chain (estimate) | 11 g | 14 g |

The pendants sold today for the same purpose are, as far as is remembered here, discs of
plastic or aluminium a few centimetres across; none was looked up for this document, so no
size or weight of theirs is quoted.

## Colours

The stone and the light under it are chosen together, when the pendant is ordered: red,
green or blue (draft). It is a choice of two parts at assembly, the glass and the LED, and
of the two resistors that set the LED's currents. No net changes and the firmware does not
know which colour it is.

It is not a colour the wearer changes from the phone, on purpose. That would take a
three-colour LED driven by firmware, and the glow would then depend on code: today its
switch is the microphones' supply rail itself, which is what lets the design say that
nothing can listen in the dark. A clear stone over a firmware-driven light is a different
product with a weaker promise.

What the two new colours cost is not known:

- A green or blue LED needs about 2.6 to 3 V where the red one needs 1.8 V (typical figures,
  not read from a datasheet). The light is fed from the cell, which falls to about 3 V
  before the protection cuts it off, so the green and blue stones may dim as the cell
  empties. Feeding the light from a boosted rail would cure it; the circuit has none.
- The eye is several times more sensitive to green than to red or blue, so the three
  colours will not want the same current for the same glow. The power budget is written
  for the red one.
- Only the red parts are chosen: the LED is the ring's, and red glass is what the model
  and the drawings assume.

## Requirements

| Requirement | Source |
| --- | --- |
| Everything the band must do: always listening, 2 days between charges (5 the stretch goal), nothing lost while the phone is away for a working day, a light whenever the microphones have power, a mute that cuts their power, Opus at about 16 kbit/s, Bluetooth LE, one phone, no server of ours, firmware the owner can rebuild | `manent-band`, from `mnemo-band` |
| Same circuit and same pins as the band, so that one firmware runs on both | this document |
| Worn on a chain, over the clothes | this document |
| An oval case of metal and glass, 40 x 26 x 9.5 mm, about 11 g | draft, from the space budget |
| The light shines through the stone | draft |
| Stone and light in red, green or blue, chosen at order | draft |
| Closed case, charged through pads on its back; no socket | draft, as the band |
| Button in the rim, pressed from the side | draft |
| No vibration motor | draft, as the band |

## Button

The band's gestures, unchanged:

| Gesture | Meaning | Handled by |
| --- | --- | --- |
| Short press | Mark this moment | firmware |
| Hold 2 s | Mute, or listen again | firmware; muting switches the microphone rail off |
| Press while in ship mode (96 ms) | Wake from storage | power chip |
| Hold 10 s | Power cycle: the way out of a hung firmware | power chip |

The switch is a side-push part under the board, at its edge, and a pusher in the rim reaches
it. It is on the side and not on the back or under the stone for three reasons: a pendant
lies on a chest and is leaned on, so a button on the back would press itself; a stone that
moves needs a seal around its whole edge; and a pinch across the width of the oval, thumb
against the opposite side, is a gesture nothing else makes by accident.
Without a motor, the only confirmation of a mute is the stone going dark.

## Light

As on the band: one LED with two levels, a steady glow of about 0.05 mA whose switch is
driven by the microphones' supply rail and not by firmware, and a bright level of about
0.5 mA that firmware adds while sound is being recorded. If a microphone has power the
stone glows, and there is no code path that can listen in the dark.

What changes is the optics. The band shows its light through a pipe about a millimetre
wide; here the same light, in the colour of the stone, spreads through a frosted stone of
about 700 mm2. The glow may
need more current to be seen at all, or less, because a large dim surface is easier to
notice than a small bright point. Nobody knows until an LED is put under a piece of glass of
its colour: it is the first thing to try, for each of the three, and it costs nothing.

## Blocks

```
back pads --springs--TVS-- VBUS --> [ nPM1304 ] <--> cell (+ protection)
                                     |  |  |
                        1.8 V buck --+  |  +-- load switch 2 --> flash supply
                                     |  +----- load switch 1 --> microphone supply --> glow
                                     v
   pusher --+--> SHPHLD          [ nRF54L15 ] --PDM--> microphone A, microphone B
            +-|<|-> wake            |  |  |
                               SPI --+  |  +-- matching -- tuning -- antenna
                                v       +-- bright light
                          512 Mbit flash
```

## Parts

The band's, with one change: the switch.

| Block | Part | Size (mm) | Confidence |
| --- | --- | --- | --- |
| Microcontroller | Nordic nRF54L15, QFN48 | 6 x 6 x 0.85 | as in `manent-band` |
| Power | Nordic nPM1304, QFN32 | 5 x 5 x 0.85 | as in `manent-band` |
| Flash | Winbond W25Q512NW, WSON-8 | 8 x 6 x 0.8 | from memory: part number, package and height to confirm |
| Microphones | 2 x TDK T5838 | 3.5 x 2.65 x 0.98 | verified |
| Switch | Panasonic EVQP7J01P, side push, the card's part | 3.5 x 2.9 x 1.35 | verified from the catalogue, as for the card |
| Light | Rohm SML-P11VT (red); green and blue parts to choose | 1.0 x 0.6 x 0.2 | red: verified at 1 mA, dimmer is from curves; the others: nothing read yet |
| Cell protection | ABLIC S-82A1A | 1.4 x 1.4 | verified |
| Charging input | Infineon ESD230-B1-W0201 | 0.58 x 0.28 | verified |
| Cell | flat LiPo pouch, 401525 class | 25 x 15 x 4 | trade size code; capacity estimated |

The full list with part numbers is `electrical/out/bom.csv`. Why each part was chosen, the
microcontroller pin table and the rules the build enforces on it are in the band's design
document and hold here unchanged: `electrical/gen/checks.py` is the same file.

## Case and assembly

- From the chest outwards: back cover, cell, board, parts, stone. The board is an ellipse
  37.4 x 23.4 mm, 0.6 thick. On the face towards the stone: the chips, the light, the
  antenna and the small parts. Under it, around the cell: the two microphones, the switch,
  the four spring contacts and the pads for the cell tabs.
- A rectangular cell in an oval case loses its corners' worth of room. The cell lies
  centred, which loses least, and the four pieces of board it leaves uncovered are all
  used: a microphone under each tip, the antenna along one long side, the switch and the
  contacts along the other.
- The microphones hang under the board on its long axis, 33 mm apart, each with a hole
  through the board, a gasket between board and rim, and a hole in the rim behind a
  membrane. The sound turns a corner between the hole in the board and the hole in the
  rim: that channel is not designed.
- The antenna is on one long edge, in front of the microcontroller, with no copper under or
  beside it on any layer, and it is the edge away from the switch and the contacts. It looks out through the
  stone and through the resin back; the titanium rim goes all round it. See "Radio".
- The pendant is assembled from the back, like a watch: the stone is set in the rim first,
  then the board with its cell goes in and the back cover closes it. How the cover is held
  and sealed is open.
- Charging: the pendant lies face up in a dish with four spring pins. The bail lets it in
  one way only, so there is no reverse polarity to protect against. Two pads charge, two
  carry SWDIO and SWDCLK: it can be reprogrammed closed. The chain stays on.

Whether it all fits is in [space-budget.md](space-budget.md). In short: the 40 x 26 oval
holds the band's 120 mAh cell with 0.2 mm of height to spare; 2 mm more width would take a
135 mAh cell and 5 mm more a 160 mAh one.

## Board

`electrical/kicad/pendant.kicad_pcb`: four copper layers, an ellipse 37.4 x 23.4 mm, seen
from the front with the bail on the left. Top copper faces the stone, bottom copper faces
the cell, the first inner layer is a ground plane. There is no ground along the antenna's
stretch of the edge on any layer.

It is made the way the band's is, by the same scripts with an ellipse for an outline:

- The parts the case decides are where the fit model puts them. The light has the centre
  of the board. The microcontroller sits beside it and has the half towards the bail to
  itself, turned so that its antenna pin faces the antenna. The other half holds the power
  chip, next to the cell tabs, and the flash, on the side of the microcontroller's
  fast-SPI pins. The rest are placed by
  a script, each as near as it can get to the pads it connects to, 0.35 mm between land
  patterns and 0.4 mm from the edge.
- Every connection is routed by Freerouting and the result is kept in
  `electrical/kicad/pendant.ses`, so that `make board` rebuilds the same board. With the two
  Nordic chips side by side the router never finished, in fourteen runs; with the power
  chip moved to the other half of the board it finished on the seventh. The first
  inner layer is closed to the router. Supplies are 0.15 mm wide, signals 0.1 mm, and the
  radio line 0.205 mm, which is 50 ohm on an assumed stack.
- KiCad's check finds no open connection, no rule violation and no difference between
  board and schematic.

Everything the band's design document says its board is not, this one is not either:
nobody chose the path of the radio line, laid out the converter loops or checked the
return paths; the QFN land patterns are KiCad's stock ones and differ from Nordic's in the
ways listed there; there are no vias under the chips; the rules and the layer stack are
assumptions. Two things are worse here. The footprint of the switch is a placeholder, as
are those of the antenna, the contacts and the cell tabs. And the antenna sits inside a
ring of metal, which no rule check knows about.

It is a board to look at and to measure the placement against, not one to order.

## Power

In [power-budget.md](power-budget.md): the band's figures on the pendant's cells. On the
120 mAh cell, about six days on a typical day at the nominal figures and between two and
fifteen across the cases in the table. The light is a quarter of it, and the stone may move
that figure either way.

## Radio

Unknown until measured, and harder than the band's. The band is a plastic pod; this is an
antenna inside a closed loop of titanium, a few millimetres from a body that absorbs at
2.4 GHz. Watches with metal cases work, with care: some use the case itself as the antenna.
Three ways out are open, in order of cost: tune the chip antenna in its real surroundings
and accept what range it gives; cut the rim once and use it as the antenna; give up the
metal rim for ceramic. Until a case exists and is measured on a person, the radio is the
largest risk in this design.

## Sound

Also unknown, and probably better than the band's. A wrist moves, rubs against sleeves and
is often under a table; a pendant hangs still, in the open, 15 to 20 cm under the mouth.
What can go wrong is specific: the pendant swings and taps against buttons and zips, a scarf
or a coat covers it, and a pendant worn under a shirt hears cloth. It is meant to be worn
over the clothes, where its light can also be seen.

## Prior art

| Product | What it shows |
| --- | --- |
| Bee (Amazon), with its clip | The same electronics as a wristband worn on the collar: see `manent-band` |
| Limitless Pendant | A disc on a magnetic clip or a cord, worn on the chest, recording all day |
| Friend | A disc on a cord with a light in its face |
| Omi | Open hardware, worn as a pendant: two T5838 and wake-on-sound, as here |

Written from memory on 2026-11-24: no product page, review or teardown was read for this
table, and sizes, weights and battery lives are not quoted for that reason. The band's
document has what was actually read about Bee.
