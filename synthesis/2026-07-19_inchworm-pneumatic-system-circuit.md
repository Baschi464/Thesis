# Inchworm pneumatic system + control circuit

This is the box that drives the robot. The soft robot itself has 3 chambers +
2 suction cups = 5 things that need their own pressure, and some of them need
*negative* pressure (vacuum for the cups). The pneumatic system was over-built
to **8 independent channels** so it could drive this robot and future ones.

## How a channel works (the core idea)
Every channel is just: **two on/off valves + one pressure sensor**, sitting
between two shared pumps (one air pump that pushes, one vacuum pump that
pulls) and the soft robot. The two valves are the channel's "in" and "out"
doors:
- **Inflate** → open the inflation valve, run the air pump, keep the exhaust
  valve shut. Air goes in.
- **Deflate** → open the exhaust valve, run the vacuum pump, keep the
  inflation valve shut. Air comes out.
- **Hold** → shut both valves. The pressure sensor watches the trapped air and
  the channel just sits at whatever pressure it reached (within ±1 kPa).

Sharing two pumps across all 8 channels (instead of 16 dedicated pumps) is
the key cost/size win, borrowed from Xiao et al. The valves do the routing;
the pumps just provide "push" and "pull" on demand.

## How the electronics implement that
An Arduino Mega can't drive solenoid coils directly, so the design stacks a
custom shield on it:
- **Valves:** 16 coils (8 channels × 2). They're switched by two **ULN2803A**
  chips — each an 8-channel low-side driver. The coils sit on 12 V; the ULN
  sinks them to ground and its COM pin catches the coil kick-back. The actual
  pin map is defined in firmware: per channel k, inflation valve =
  `VALVES_POS[k]` (pins 42,44,46,48,50,52,51,53) and exhaust valve =
  `VALVES_NEG[k]` (pins 36,34,32,30,28,26,24,22). **Note the schematic and the
  built board disagree:** the KiCad schematic routed the valve inputs through
  D22–D37 (and left D42–D53 unconnected), but the hand-soldered perfboard was
  wired per the firmware pins above. The firmware is treated as ground truth
  for the as-built robot; the schematic is the earlier plan.
- **Pumps:** positive (air) pump on `PIN_PUMP_POS = D13`, vacuum pump on
  `PIN_PUMP_NEG = D12`, each through an IRLZ44N MOSFET.
- **Sensors:** 8 pressure sensors, but the Arduino's own analog pins aren't
  great, so two **ADS1115** 16-bit ADC modules read them over I²C (one at
  address 0x48, the other at 0x49, 4 sensors each). Two wires (SDA=D20,
  SCL=D21) carry all 8 readings.
- **Pumps:** the 2 shared pumps are bigger loads, so they get their own
  **IRLZ44N** MOSFETs (logic-level, so the Arduino can switch them) with
  1N4007 flyback diodes and a pair of fat 0.5 F buffer caps to soak up the
  inrush when pumps/valves slam on.
- **Power:** a 12 V / 10 A switching supply runs the valves and pumps; a
  step-down converter makes the 5 V logic rail for the brain and sensors.

The whole thing was laid out compactly in KiCad and checked as a 3D render
before soldering, which is why there's a render image separate from the photo
of the finished, wired box.

## Reading the schematic honestly (important caveats)
The KiCad schematic is a **planning drawing**, not a fully rule-clean netlist.
I built the wiring tables from the exported netlist and corrected/annotated a
few things instead of transcribing them blindly:
1. **The GPIO → valve-driver mapping is exact and trustworthy** (D22–D37 →
   ULN inputs). That's the backbone table.
2. **Rail labels are loose (resolved).** Three physical rails: **5 V logic**
   (step-down converter → Arduino, ADS1115, sensors), **12 V** (PSU direct →
   solenoid valves), **24 V** (boost converter → the two shared pumps). The
   schematic lumps the 5 V logic/sensor supply under the "+12V" net label, and
   its "+24V" annotation is the boost-converter output (the converter isn't
   drawn as a component). The ADS1115/sensors are 5 V parts, so the text
   states 5 V logic / 12 V valves / 24 V pumps rather than transcribing the
   labels.
3. **Sensor OUT lines are drawn merged** onto one net (the "3 channels drawn,
   rest copied" simplification you mentioned), so the exact sensor→ADC-channel
   order comes from the board layout, not the netlist. Same for the
   valve-output→connector order. Both are footnoted in the tables.

## Implementation (concrete next steps)
**Figures to add** (drop into `synthesis/figures/`, then uncomment the
`\includegraphics` lines in the `.tex`):
- `pneumaticSchematic.png` — KiCad schematic export (Fig. circuit).
- `electronicsRender.png` — KiCad 3D render (Fig. render).
- `inflation.png`, `deflation.png`, `holding.png` — the three valve-state
  diagrams (Fig. states).
- Confirm `figures/pneumaticSystemFull.eps` (already staged) is the correct
  full-system photo; replace if not.

**Done:** the valve table is now channel-explicit from the firmware pin map
(inflation = VALVES_POS, exhaust = VALVES_NEG, pumps on D13/D12). Still open:
the **sensor→channel order** isn't in the provided firmware snippet, so the
sensor table keeps the ADS-address/channel convention (channels 1–4 on 0x48,
5–8 on 0x49); supply the I²C read order if you want it made exact.

**Open decision for the author:** the schematic (D22–D37) and the as-built
firmware pins (42–53 / 22–36) disagree. The text now states the firmware is
as-built and the schematic was a preliminary plan. If instead the schematic
should be the authority (e.g. you plan to rewire/reflash), tell me and I'll
flip it — but then the displayed schematic figure and the firmware won't match.

**Preamble:** needs `\usepackage{multirow}` and `\usepackage{makecell}` (shared
with the actuator-FEM entry).
