# Pneumatic coupling: connector, S/U routing, inlet asymmetry (2026-07-06)

Type: design decision + theoretical idea (hedged) + experimental observation
Companion LaTeX: `2026-07-06_pneumatic-coupling-connector.tex`

## High-level explanation

The connector between body and tail is the distinctive piece of hardware
in this robot. It does three things at once: holds the two segments
together, plumbs their chambers into each other, and carries the inlet.

**S vs U is chosen by plumbing, not by extra valves.** Inside the
connector there are sub-millimeter (<1 mm) channels linking body chambers
to tail chambers, in two topologies:

- **Crossed channel** → a body chamber is connected to a tail chamber on
  the *opposite* side. One input inflates opposite sides of the two
  segments → they curve in opposite directions → **S shape** (planar
  steering/undulation).
- **Uncrossed channel** → same-side chambers connected. Both segments
  curve the same way → **U shape** (lifting out of plane, wall
  transition).

So the same single input line produces either whole-unit deformation mode
just by which chamber pair you address.

**Why the body bends more than the tail.** The inlet sits closer to the
body side. The tail is fed only through the narrow channel, so at
steady state the body bends visibly more. For modeling we abstract this
as P_t = α·P_b with 0 < α ≤ 1, α to be fitted experimentally.

**Honesty box (keep this in the paper):** we have NOT measured the two
internal pressures independently. "Viscous loss in the narrow channel" is
a plausible mechanism, not a verified one. The defensible claim is:
*inlet placement + narrow channels ⇒ asymmetric effective actuation*.
Anything stronger needs two pressure sensors.

**Demonstrated numbers:** S-shape on the assembled robot at ~10–11 kPa,
~75° per segment at 11 kPa. U-shape (lifting against gravity, posterior
feet attached) at 10.5–11.4 kPa including tip-loaded cases. Every
experiment frame includes the CKD PPX pressure display so pressure and
shape can be correlated frame by frame.

## Implementation

- [ ] Fix figure paths (`figures/bodytailconnector.png`,
      `figures/bodytailconnectorsection.png`, `figures/lizardBodyS.jpeg`,
      `figures/lizardBodyU.jpeg`) and uncomment.
- [ ] **Confirm exact channel topology** (open question from this
      session): which body chamber connects to which tail chamber; is one
      pair crossed and one pair straight-through; is the third chamber
      pair blind/unconnected? The CAD section suggests the crossing tube
      links the two upper chambers and the lower chamber has a straight
      passage — confirm before the paper's connector figure is captioned
      definitively.
- [ ] Record connector channel length and exact diameter, connector
      material, and whether the connector is 3D printed.
- [ ] Future experiment for α: instrument body and tail with independent
      pressure sensing (or measure tail pressure at a second port) and
      identify α across the working range; check whether α is
      pressure-dependent (a single constant may not hold).
- [ ] Per-segment bending angles for the S and U photo series are
      deferred to the model/reconstruction analysis (explicit user
      decision in this session) — do not backfill numbers into the
      hardware section.
