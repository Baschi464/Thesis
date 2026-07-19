# Inchworm actuator — bending characterization

This is the reality check on the FEM. The simulation promised low-pressure
bending; the experiment measures what the real cast actuator actually does.

The setup is deliberately simple: hang the actuator vertically, clamp it,
push air into a single chamber with a hand syringe, and read the pressure off
an in-line sensor. A camera films the bend and ImageJ measures the angle
frame by frame off the video. Crucially the actuator bends **against
gravity** here, so this is a conservative number — on a real stride the bend
is often gravity-assisted.

The headline result: **180° of bend at ~15.5 kPa** with just one chamber
pressurized. That is the single most-quoted number of the whole platform,
and it's the anchor the lizard chapter refers back to when it says its
miniaturized segment reaches ~180° at ~15 kPa. Low pressure, full fold, one
chamber — that's what makes the single-actuator gait feasible.

## Implementation

No further implementation needed — the characterization is complete and the
result (180° at 15.5 kPa, single chamber, against gravity) is final. Figure
already staged: `figures/experiment.eps`.
