# Open questions

The band's list (`manent-band/docs/open-questions.md`) holds here too, wherever it speaks
of the circuit, the parts, the firmware or the law: the electronics are the same. This file
lists only what the pendant adds.

## Decisions for the project owner

Each has a draft answer in the design, chosen so the scripts had something to check.

| Question | Why it matters | Draft |
| --- | --- | --- |
| The shape | An oval takes a rectangular cell with the least waste; a disc or a drop would need another cell or more room | oval cabochon, 40 x 26 mm |
| The colours of the stone | Each stone needs a light of its own colour; every colour is one more glass and one more LED to stock | red, green and blue, chosen at order |
| A colour set from the phone | It needs a three-colour LED driven by firmware, and the glow would no longer be wired to the microphones' supply | no |
| Glass or sapphire | Sapphire does not scratch and costs several times more; both are cut as cabochons | mineral glass |
| The metal of the rim | Titanium is the ring's metal and is light; silver and gold are what jewellers work; any metal ring surrounds the antenna | polished titanium |
| A metal rim at all | It is what makes it a jewel and it is the largest risk to the radio | metal, to be measured |
| Size | 40 x 26 holds about 120 mAh; 42 x 31 about 160 mAh and weighs about 2 g more | 40 x 26 |
| Where the button goes | Side, back, or the stone itself | a pusher in the rim, on one side |
| Fixed bail or hinged | A hinged bail hangs better; a fixed one keeps the light facing out | fixed |
| Chain | Length decides where the microphones are; a chain is also a thing people already own | not included in the design; 45 to 50 cm assumed |
| Worn under clothes | The light is hidden and the microphones hear cloth | not supported: over the clothes |
| Name | The band is "Manent band" | Manent pendant; "Pendente" on the site |

## To confirm from documents

| Item | Where to look |
| --- | --- |
| A side-push switch about 3.5 x 2.9 mm: part, land pattern, force, travel, sealing | Panasonic, Alps Alpine, C&K catalogues |
| Titanium grade for a part worn on skin, and whether a polished rim this thin can be machined or must be cast | a jewellery or watch-case maker |
| Glass cabochons 38 x 24 mm with a flat frosted back, in red, green and blue: stock sizes, or cut to order | suppliers of glass and synthetic stones |
| Green and blue LEDs in the red one's package: forward voltage at 0.05 and 0.5 mA, brightness | Rohm and other makers' datasheets |
| Rules for nickel release and for lithium cells in jewellery worn on the body | EU regulations, to be read |
| What the pendants on sale contain and how long they last | teardowns or radio approval files |

## To measure, no pendant needed

1. An LED under a piece of frosted glass of its colour, for red, green and blue: the
   current at which the glow is seen across a table indoors, and outdoors, and how each
   colour dims between a full cell and an empty one.
2. A chip antenna on a development board inside a metal ring of this size, on a chest:
   how much range is left.
3. A T5838 breakout hung at chest height, over and under a shirt: speech across a table,
   and the noise of cloth and of the chain.

## To measure on a pendant

1. Radio range and antenna efficiency in the closed case, worn.
2. Microphones: the sound channel through the rim, swinging and tapping, a covered port.
3. How often it turns over, with this bail and with a hinged one.
4. The pusher: feel, accidental presses when leaned on or hugged.
5. Heat while charging in a closed metal case; sweat and water at the back cover and the holes.
6. The days between charges on a real day.

## Not designed yet

Everything the band lists, and: the rim as a part that can be made, with the seat of the
stone and the way it is closed over it; the back cover, its joint and its seal; the pusher
and its seal; the two sound channels, gaskets and membranes; the bail; the dock; the stone
itself with a supplier; the antenna in its ring of metal.
