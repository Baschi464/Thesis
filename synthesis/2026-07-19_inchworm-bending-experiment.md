# Inchworm actuator — bending characterization

This is the reality check on the FEM. The simulation promised low-pressure
bending; the experiment measures what the real cast actuator actually does.

The setup is deliberately simple: hang the actuator vertically, clamp it,
push air into a single chamber with a hand syringe, and read the pressure off
an in-line sensor. A camera films the bend and ImageJ measures the angle
frame by frame off the video. Crucially the actuator bends **against
gravity** here, so this is a conservative number — on a real stride the bend
is often gravity-assisted.

The headline result: **180° of bend at ~14.8 kPa** with just one chamber
pressurized. That is the single most-quoted number of the whole platform,
and it's the anchor the lizard chapter refers back to when it says its
miniaturized segment reaches ~180° at ~15 kPa. Low pressure, full fold, one
chamber — that's what makes the single-actuator gait feasible. (The RoboMech
paper rounded this to 15.5 kPa; the raw data — and the existing lizard
characterization § — put the 181° peak at 14.8 kPa, so the thesis uses 14.8
for internal consistency. Full loop tabulated in the appendix.)

## Implementation

No further implementation needed — the characterization is complete and the
result (180° at 14.8 kPa, single chamber, against gravity) is final. The §IV
figure now uses the decomposed `figures/decomposed/experimentDiagram.png`
(setup) and `figures/decomposed/inflationvsdeflation.png` (pressure–angle
loop) instead of the compound `experiment.eps`.
