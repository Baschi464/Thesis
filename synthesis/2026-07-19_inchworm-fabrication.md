# Inchworm actuator — fabrication

This entry captures how the actuator and its feet were actually built. It was
commented out in the conference paper for space; it is reinstated here in
full because the thesis has room and the process details matter for
reproducing the part.

**The body is cast, not printed.** A mold holds three brass prisms (fan-shaped
cross-section) that leave behind the three chambers when the silicone cures.
The clever part is the wall thickness: two CNC-cut acrylic spacers hold the
brass cores exactly 0.5 mm apart, which sets the internal wall thickness —
and remember from the FEM entry that thin walls are one of the two biggest
pressure-reducing knobs, so this 0.5 mm is a deliberate optimization target,
not an arbitrary number. An acrylic outer casing keeps everything aligned
while pouring.

**Fibers go on after casting.** Inextensible fiber is wound in parallel rings
around the outside at 1.5 mm pitch, over a fresh silicone coat that glues it
down. Those rings are the strain-limiting layer that turns chamber inflation
into bending instead of ballooning.

**Caps and glue.** A resin-printed top cap carries the pressure ports; a
bottom cap closes the base. Both are bonded with KE-44T (Shin-Etsu), the same
silicone-to-rigid adhesive used throughout. Final actuator: 66 mm long, 18 mm
diameter.

**Feet = rigid core + soft lip, plus a hinge.** Each suction cup has a stiff
PEI disc in the middle so the cup ceiling doesn't cave in under vacuum, with
a soft silicone lip cast around it for the seal. The soft hinge mentioned in
the concept entry is a *second* silicone lip cast onto the actuator tips; the
cups bond to those lips, so the foot can passively tilt and stay flat when the
actuator bends.

## Implementation

No further implementation needed — the fabrication process is complete and
documented. Figures already staged: `figures/mold.eps`,
`figures/suctioncup.eps`. If the thesis later wants a photo of the finished
actuator, `figures/InchwormFront.eps` is staged and available (content to be
confirmed before use).
