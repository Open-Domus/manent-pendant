"""The Manent pendant circuit as data: parts, values and nets.

It is the band's circuit (manent-band, electrical/gen/design.py), net for net, so that one
firmware runs on both. Two things differ and neither changes a net: the switch is a side-push
part, pressed through the rim, and the notes say where each part sits in an oval case.
Anything not confirmed carries a Note saying so; the notes end up in the bill of materials.
"""
from collections import defaultdict

from .emit import Component, Pin, SymDef, two_pin
from .footprints import LIB_NAME, footprint_of

SHEETS = [("power", "Power and charging"), ("mcu_rf", "Microcontroller and radio"),
          ("audio", "Microphones"), ("storage", "Flash memory"), ("ui", "Button, light, pads")]

TYPES = {"pi": "power_in", "po": "power_out", "p": "passive", "i": "input", "o": "output",
         "b": "bidirectional", "t": "tri_state", "nc": "no_connect"}


def ic(name, prefix, spec, width=30.48):
    """spec: lines of 'number name type side'."""
    pins = tuple(Pin(n, nm, TYPES[t], s) for n, nm, t, s in (line.split() for line in spec.strip().splitlines()))
    return SymDef(name, prefix, pins, width)


R, C, L, D, FB = (two_pin(n, p) for n, p in (("R", "R"), ("C", "C"), ("L", "L"), ("D", "D"), ("FB", "FB")))
LED = two_pin("LED", "D")
XTAL = two_pin("XTAL", "Y")
XTAL4 = ic("XTAL4", "Y", "1 X1 p L\n3 X2 p R\n2 CASE p L\n4 CASE p R", width=10.16)
SW = two_pin("SW", "SW")
CELL = two_pin("CELL", "BT")
TVS = two_pin("TVS", "D")
PAD = SymDef("PAD", "TP", (Pin("1", "~", "passive", "L"),), width=5.08)
CONTACT = SymDef("CONTACT", "J", (Pin("1", "~", "passive", "L"),), width=5.08)
ANT = SymDef("ANTENNA", "AE", (Pin("1", "FEED", "passive", "L"),), width=10.16)
FLAG = SymDef("PWR_FLAG", "#FLG", (Pin("1", "pwr", "power_out", "L"),), width=5.08, virtual=True)
NFET = ic("NMOS", "Q", "1 G i L\n2 S p R\n3 D p R", width=10.16)

# Pin tables read on 2026-11-23 from Nordic's product specifications (see parts/pins).
SOC = ic("nRF54L15-QFAA", "U", """
1 P1.00/XL1 b L
2 P1.01/XL2 b L
3 P1.02 b L
4 P1.03 b L
5 P1.04 b R
6 P1.05 b R
7 P1.06 b R
8 P1.07 b R
9 P1.08 b R
10 VDD pi L
11 P2.00 b R
12 P2.01 b R
13 P2.02 b R
14 P2.03 b R
15 P2.04 b R
16 P2.05 b R
17 P2.06 b R
18 P2.07 b R
19 P2.08 b R
20 P2.09 b R
21 P2.10 b R
22 VDD pi L
23 P0.00 b L
24 P0.01 b L
25 SWDIO b L
26 SWDCLK i L
27 P0.02 b L
28 P0.03 b L
29 P0.04 b L
30 nRESET i L
31 ANT p L
32 VSS_PA pi L
33 DECRF p L
34 XC1 p L
35 XC2 p L
36 VDD pi L
37 P1.09 b R
38 P1.10 b R
39 P1.11 b R
40 P1.12 b R
41 P1.13 b R
42 P1.14 b R
43 DECA p L
44 VSS pi L
45 DECD p L
46 DCC p L
47 VDD pi L
48 VDD pi L
49 VSS pi L
""")

PMIC = ic("nPM1304-QEAA", "U", """
1 VOUT1 po R
2 PVSS1 pi L
3 SW1 p R
4 PVDD pi L
5 SW2 p R
6 PVSS2 pi L
7 GPIO0 b R
8 GPIO1 b R
9 GPIO2 b R
10 GPIO3 b R
11 GPIO4 b R
12 VDDIO pi L
13 SDA b R
14 SCL i R
15 SHPHLD i L
16 VSET2 p L
17 VSET1 p L
18 NTC i L
19 VBAT p L
20 VSYS po L
21 VBUS pi L
22 VBUSOUT p L
23 CC1 i L
24 CC2 i L
25 LED0 p R
26 LED1 p R
27 LED2 p R
28 LSIN1 pi R
29 LSOUT1 po R
30 LSIN2 pi R
31 LSOUT2 po R
32 VOUT2 p R
33 AVSS pi L
""")

PROT = ic("S-82A1A", "U", "1 VSS pi L\n2 VDD pi L\n3 VINI i L\n4 VM i R\n5 CO o R\n6 DO o R", width=20.32)
MIC = ic("T5838", "MK", "7 VDD pi L\n3 GND pi L\n2 SELECT i L\n6 CLK i R\n1 DATA t R\n5 THSEL i R\n4 WAKE o R", width=20.32)
# The pin order every 8-pin serial NOR flash shares; pad 9 is the exposed pad.
FLASH = ic("SPI-NOR-8", "U", """
8 VCC pi L
4 GND pi L
9 EP p L
1 /CS i R
6 CLK i R
5 DI(IO0) b R
2 DO(IO1) b R
3 /WP(IO2) b R
7 /HOLD(IO3) b R
""", width=25.4)

# Which SoC pin does what. The checks in checks.py verify the clock-pin and port rules.
SOC_NETS = {
    "P0.00": "BTN_WAKE", "P0.01": "PMIC_INT", "P0.02": "I2C_SDA", "P0.03": "I2C_SCL", "P0.04": "LED_AUX",
    "P1.00/XL1": "XL1", "P1.01/XL2": "XL2",
    "P1.04": "PDM_CLK", "P1.05": "PDM_DIN", "P1.06": "MIC_A_THSEL", "P1.07": "MIC_A_WAKE",
    "P1.09": "MIC_B_THSEL", "P1.10": "MIC_B_WAKE",
    "P1.11": "UART_TX", "P1.12": "UART_RX", "P1.13": "MIC_EN",
    "P2.01": "SPI_SCK", "P2.02": "SPI_SDO", "P2.04": "SPI_SDI", "P2.05": "FLASH_CS",
}

UNVERIFIED_CAPS = "Value from Nordic's reference list; which net each capacitor sits on is not confirmed"


def build() -> list[Component]:
    comps: list[Component] = []
    count = defaultdict(int)

    def add(sym, value, sheet, nets, mpn="", mfr="", package="", note="", dnp=False):
        count[sym.prefix] += 1
        if isinstance(nets, (list, tuple)):
            nets = {p.number: n for p, n in zip(sym.pins, nets)}
        fields = {"MPN": mpn, "Manufacturer": mfr, "Package": package, "Note": note}
        comps.append(Component(f"{sym.prefix}{count[sym.prefix]}", sym, value, sheet, nets,
                               {k: v for k, v in fields.items() if v}, dnp))

    def by_name(sym, mapping):
        """Nets keyed by pin name; pins not named get a no-connect."""
        return {p.number: mapping.get(p.name) for p in sym.pins}

    cap = lambda v, net, sheet, pkg="0402", note="", **kw: add(C, v, sheet, (net, "GND"), package=pkg, note=note, **kw)
    res = lambda v, a, b, sheet, note="", pkg="0402", **kw: add(R, v, sheet, (a, b), package=pkg, note=note, **kw)

    # ---- power (as on the ring) --------------------------------------------------------
    add(PMIC, "nPM1304", "power", by_name(PMIC, {
        "VBUS": "VBUS", "VBUSOUT": "VBUSOUT", "CC1": "GND", "CC2": "GND", "VBAT": "VBAT", "NTC": "GND",
        "VSYS": "VSYS", "PVDD": "VSYS", "VDDIO": "V1V8", "AVSS": "GND", "PVSS1": "GND", "PVSS2": "GND",
        "VSET1": "VSET1", "VSET2": "GND", "SHPHLD": "BTN_N", "SW1": "SW1", "VOUT1": "V1V8",
        "VOUT2": "GND", "LSIN1": "V1V8", "LSOUT1": "VMIC", "LSIN2": "V1V8", "LSOUT2": "VFLASH",
        "SCL": "I2C_SCL", "SDA": "I2C_SDA", "GPIO0": "PMIC_INT", "GPIO1": "MIC_EN",
    }), mpn="nPM1304-QEAA-R7", mfr="Nordic Semiconductor", package="QFN-32 5x5, 0.5 mm pitch",
        note="Charges at up to 100 mA: enough for these cells. "
             "BUCK2 unused: VSET2 grounded as documented; SW2 open and VOUT2 grounded are not confirmed. "
             "LED0-2, GPIO2-4 left open: not confirmed. NTC grounded: set DISABLENTC in firmware")
    add(L, "2.2uH", "power", ("SW1", "V1V8"), mpn="to choose", package="0806",
        note="Nordic asks for DCR under 0.4 ohm in 0806 (2.0 x 1.6 mm); part to choose")
    res("47k", "VSET1", "GND", "power", note="Sets BUCK1 to 1.8 V at power-on")
    cap("1uF 25V", "VBUS", "power", pkg="0603", note=UNVERIFIED_CAPS)
    cap("1uF", "VBUSOUT", "power", note=UNVERIFIED_CAPS)
    cap("10uF", "VBAT", "power", pkg="0603", note=UNVERIFIED_CAPS)
    cap("10uF", "VSYS", "power", pkg="0603", note=UNVERIFIED_CAPS)
    cap("10uF", "V1V8", "power", pkg="0603", note="Buck output: at least 4 uF effective")
    cap("100nF", "V1V8", "power", note="VDDIO")
    cap("1uF", "VMIC", "power", note="Load switch output; value to confirm")
    cap("1uF", "VFLASH", "power", note="Load switch output; value to confirm")
    res("10k", "I2C_SCL", "V1V8", "power")
    res("10k", "I2C_SDA", "V1V8", "power")
    add(TVS, "5.5V bidirectional", "power", ("VBUS", "GND"), mpn="ESD230-B1-W0201", mfr="Infineon", package="0201")
    add(CONTACT, "charge +", "power", ("VBUS",), mpn="to choose", package="spring contact",
        note="To a pad on the back cover. The bail lets the pendant into its dock one way only")
    add(CONTACT, "charge -", "power", ("GND",), mpn="to choose", package="spring contact")
    add(FLAG, "PWR_FLAG", "power", ("VBUS",))
    add(FLAG, "PWR_FLAG", "power", ("GND",))
    add(FLAG, "PWR_FLAG", "power", ("CELL_P",))
    add(FLAG, "PWR_FLAG", "power", ("CELL_N",))
    # Cell and protection (only if the cell ships without its own protection board)
    add(CELL, "LiPo pouch 3.7 V", "power", ("VBAT", "CELL_N"), mpn="401525 class", mfr="to choose",
        note="Size and capacity depend on the case; see docs/space-budget.md")
    add(FLAG, "PWR_FLAG", "power", ("VBAT",))
    res("330", "VBAT", "CELL_P", "power", note="Protector supply filter")
    cap("100nF", "CELL_P", "power")
    comps[-1].nets = {"1": "CELL_P", "2": "CELL_N"}
    add(PROT, "S-82A1A", "power", by_name(PROT, {"VSS": "CELL_N", "VDD": "CELL_P", "VINI": "SENSE",
                                                 "VM": "VM", "CO": "PROT_CO", "DO": "PROT_DO"}),
        mpn="S-82A1AAG-A6T5S (variant to confirm)", mfr="ABLIC", package="DFN-6 1.4x1.4",
        note="Fit only if the cell has no protection of its own; thresholds to match the charge voltage")
    res("0.25", "CELL_N", "SENSE", "power", note="Overcurrent sense: about 200 mA trip (calculated, not from a datasheet)")
    res("470", "VM", "GND", "power")
    add(NFET, "N-MOSFET", "power", {"1": "PROT_DO", "2": "SENSE", "3": "FET_MID"}, mpn="to choose",
        note="Discharge FET; a dual common-drain part in about 1x1 mm")
    add(NFET, "N-MOSFET", "power", {"1": "PROT_CO", "2": "GND", "3": "FET_MID"}, mpn="to choose", note="Charge FET")

    # ---- microcontroller and radio (Nordic QFAA reference circuit, configuration 1: DC/DC, no NFC) --
    # The reference schematic is a picture: values and part numbers were read from its labels,
    # which net each one sits on was not. The wiring below follows the ring's verified CSP circuit
    # with the one difference the pin table states: DECRF is joined to DECA.
    REF = "Value from Nordic's QFN48 reference; its place in the circuit is assumed from the CSP47 one"
    add(SOC, "nRF54L15", "mcu_rf", by_name(SOC, {
        "VDD": "V1V8", "DCC": "DCC", "DECD": "DECD", "DECA": "DECA", "DECRF": "DECA",
        "VSS": "GND", "VSS_PA": "GND", "XC1": "XC1", "XC2": "XC2", "ANT": "ANT",
        "nRESET": "NRESET", "SWDCLK": "SWDCLK", "SWDIO": "SWDIO", **SOC_NETS,
    }), mpn="nRF54L15-QFAA-R", mfr="Nordic Semiconductor", package="QFN-48 6x6, 0.4 mm pitch",
        note="Pin 49 is the exposed pad: ground")
    cap("10uF", "V1V8", "mcu_rf", pkg="0603")
    for _ in range(4):
        cap("100nF", "V1V8", "mcu_rf", pkg="0201", note="One next to each side's VDD pin. " + REF)
    add(L, "4.7uH", "mcu_rf", ("DCC", "DECD"), mpn="to choose", package="0402", note="DC/DC inductor. " + REF)
    cap("2.2uF", "DECD", "mcu_rf", pkg="0201", note=REF)
    add(FB, "ferrite bead", "mcu_rf", ("DECD", "DECA"), mpn="to choose", package="0201",
        note="The reference gives no value; the ring uses 120 ohm at 100 MHz (BLM03AG121SN1D)")
    cap("2.2uF", "DECA", "mcu_rf", pkg="0201", note=REF)
    cap("10nF", "DECA", "mcu_rf", pkg="0201", note=REF)
    add(XTAL4, "32MHz", "mcu_rf", {"1": "XC1", "3": "XC2", "2": "GND", "4": "GND"}, mpn="to choose", package="2016",
        note="2.0 x 1.6 mm, as in the reference; pads 2 and 4 are the lid, grounded: check against the part chosen. "
             "Load capacitors are inside the chip")
    add(XTAL, "32.768kHz 9pF", "mcu_rf", ("XL1", "XL2"), mpn="9HT11-32.768KDZC-T", mfr="TXC", package="2012",
        note="Fitted, as on the band: the pendant stays connected for days and there is room. "
             "Load capacitors are inside the chip")
    MATCH = "Matching network: part from the reference, order in the chain assumed"
    add(L, "2.7nH", "mcu_rf", ("ANT", "RF_A"), mpn="LQP03HQ2N7B02", mfr="Murata", package="0201", note=MATCH)
    cap("1.5pF", "RF_A", "mcu_rf", pkg="0201", mpn="GJM0335C1E1R5WB01", mfr="Murata", note=MATCH)
    add(L, "3.5nH", "mcu_rf", ("RF_A", "RF_B"), mpn="LQP03HQ3N5B02", mfr="Murata", package="0201", note=MATCH)
    cap("2.0pF", "RF_B", "mcu_rf", pkg="0201", mpn="GJM0335C1E2R0WB01", mfr="Murata", note=MATCH)
    add(L, "3.5nH", "mcu_rf", ("RF_B", "RF_50"), mpn="LQP03HQ3N5B02", mfr="Murata", package="0201", note=MATCH)
    res("0", "RF_50", "ANT_FEED", "mcu_rf", pkg="0201",
        note="Antenna tuning, series: value from measurement in a closed case, inside its metal rim, on a chest")
    cap("tune", "RF_50", "mcu_rf", pkg="0201", dnp=True, note="Antenna tuning, shunt")
    cap("tune", "ANT_FEED", "mcu_rf", pkg="0201", dnp=True, note="Antenna tuning, shunt")
    add(ANT, "2.4 GHz", "mcu_rf", ("ANT_FEED",), mpn="to choose", package="1608 chip antenna",
        note="Chip antenna or printed trace at the edge of the board; decided with the first radio measurements")

    # ---- microphones: two on one clock and one data line ---------------------------------
    for name, select, where in (("A", "GND", "the tip with the bail, towards the mouth"), ("B", "VMIC", "the opposite tip")):
        add(MIC, "T5838", "audio", by_name(MIC, {
            "VDD": "VMIC", "GND": "GND", "SELECT": select, "CLK": "PDM_CLK", "DATA": "PDM_DIN",
            "THSEL": f"MIC_{name}_THSEL", "WAKE": f"MIC_{name}_WAKE"}),
            mpn="MMICT5838-00-012", mfr="TDK InvenSense", package="3.5x2.65x0.98 bottom port",
            note=f"Microphone {name}, at {where}; SELECT at {select} picks its clock edge. "
                 "No pull resistor on DATA. Board hole 0.5-1.0 mm under the port")
        cap("100nF", "VMIC", "audio", pkg="0201", note=f"X7R, next to pin 7 of microphone {name}")

    # ---- flash ---------------------------------------------------------------------------
    add(FLASH, "W25Q512NW", "storage", by_name(FLASH, {
        "VCC": "VFLASH", "GND": "GND", "EP": "GND", "/CS": "FLASH_CS", "CLK": "SPI_SCK", "DI(IO0)": "SPI_SDO",
        "DO(IO1)": "SPI_SDI", "/WP(IO2)": "FLASH_IO2", "/HOLD(IO3)": "FLASH_IO3"}),
        mpn="W25Q512NW (ordering code to confirm)", mfr="Winbond", package="WSON-8 8x6",
        note="512 Mbit at 1.8 V; part number and package from memory, not from the datasheet. "
             "Exposed pad to ground is the usual practice, to confirm. Any 1.8 V serial NOR in this package fits")
    cap("100nF", "VFLASH", "storage")
    res("100k", "FLASH_CS", "VFLASH", "storage", note="Keeps the chip deselected while the rail rises")
    res("100k", "FLASH_IO2", "VFLASH", "storage", note="Termination in single-bit SPI to confirm")
    res("100k", "FLASH_IO3", "VFLASH", "storage", note="Termination in single-bit SPI to confirm")

    # ---- button, light, pads ---------------------------------------------------------------
    add(SW, "tactile, side push", "ui", ("BTN_N", "GND"), mpn="to choose", package="side-push SMD, about 3.5x2.9x1.35",
        note="Under the board, at its edge: a pusher in the rim presses it. Pulled up inside the PMIC (SHPHLD)")
    add(D, "Schottky", "ui", ("BTN_N", "BTN_WAKE"), mpn="RB521ZS-30", mfr="Rohm", package="0201",
        note="Pin 1 is the cathode. Anode at the SoC: keeps the PMIC pull-up voltage off the 1.8 V pin")
    add(LED, "red", "ui", ("LED_K", "VSYS"), mpn="SML-P11VT", mfr="Rohm", package="1.0x0.6x0.2",
        note="Pin 1 is the cathode. Under the stone: it lights the whole cabochon from inside. "
             "This is the red one; the green and blue pendants take an LED of their colour in the same package, to choose")
    res("33k", "LED_K", "LED_SW", "ui",
        note="Steady glow, about 0.05 mA, whenever the microphones have power; adjust after a look through the stone, for each colour")
    add(NFET, "N-MOSFET", "ui", {"1": "VMIC", "2": "GND", "3": "LED_SW"}, mpn="to choose",
        note="Gate is the microphone rail: the light is on whenever the microphones have power. Vgs(th) under 1 V")
    res("3.3k", "LED_K", "LED_HI", "ui", note="Bright, about 0.5 mA: firmware turns it on while sound is being recorded")
    add(NFET, "N-MOSFET", "ui", {"1": "LED_AUX", "2": "GND", "3": "LED_HI"}, mpn="to choose",
        note="Firmware can only add light, never remove the steady glow")
    res("100k", "LED_AUX", "GND", "ui", note="Bright light off while the SoC is in reset")
    for label, net in (("SWDIO", "SWDIO"), ("SWDCLK", "SWDCLK")):
        add(CONTACT, label, "ui", (net,), mpn="to choose", package="spring contact",
            note="Service pad on the back cover: reachable with the case closed")
    for label, net in (("nRESET", "NRESET"), ("UART TX", "UART_TX"), ("UART RX", "UART_RX"), ("1V8", "V1V8"),
                       ("GND", "GND"), ("VBAT", "VBAT"), ("VBUS", "VBUS")):
        add(PAD, label, "ui", (net,), note="Test pad on the board, for the factory test before the case is closed")
    for c in comps:
        fp = footprint_of(c)
        if fp:
            c.fields["Footprint"] = f"{LIB_NAME}:{fp}"
    return comps


def netlist(comps=None) -> dict[str, set[tuple[str, str]]]:
    nets = defaultdict(set)
    for c in comps or build():
        for pin, net in c.nets.items():
            if net is not None:
                nets[net].add((c.ref, pin))
    return dict(nets)
