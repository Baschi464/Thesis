# Coupled body–tail actuator — segment design (2026-07-06)

Type: design decision + numeric data
Companion LaTeX: `2026-07-06_coupled-bodytail-actuator-design.tex`

## High-level explanation

Body and tail are two identical copies of the small three-chamber
actuator. Each one is a 6 mm diameter silicone cylinder, 26 mm of tube
(33 mm total with end interfaces), 0.4 mm outer wall, interior split into
three 120° pie-slice chambers whose walls meet at the center. Pressurize
one slice → it bends away from that slice; pressurize two → bends between
them; all three → elongates. That's the omnidirectional part.

Two kinds of fiber do two different jobs:

1. **Circumferential loops** (parallel circles, NOT a helix), ~1.5 mm
   apart on average. They stop the tube from ballooning radially, so
   pressure goes into bending instead of bulging. "Average" because
   they're wrapped by hand: the tube is dipped in fresh silicone, the
   fiber is wound loop by loop, and the excess silicone is scraped off
   each fiber with tweezers.
2. **One central axial fiber** running through the point where the three
   internal walls meet. It makes the neutral axis inextensible, so
   inflation curves the segment instead of stretching it. Its measured
   effect is in the characterization entry.

The two segments sit on opposite faces of a rigid connector. They are
geometrically identical — the asymmetry in how much each bends comes from
the pneumatics (inlet placement + narrow channel), not from geometry.
**Naming convention decided**: the segment nearer the inlet (= the one
that bends more) is the *body*; the far one is the *tail*. Rationale:
wall transition needs the anterior part to lift/reorient strongly, so the
stronger-bending side is the front. (In the S-shape photos the body is on
the left; in the U-shape photos it's on the right; for the bare coupled
actuator, body = the side that bends more.)

## Implementation

- [ ] Fix figure paths (`figures/centralfiberTopview.jpeg`,
      `figures/centralfiberSideview.jpeg`,
      `figures/lizard_actuators_details.png`) and uncomment.
- [ ] Replace `\cite{TODO-Baschiera-inchworm}` with the real key.
- [ ] Verify BibTeX entries exist for `Yan2016ThreeChambered` and
      `Moutousi2024Omnidirectional` (both appear in the inchworm paper's
      reference list, so they should already be in `references.bib` —
      check the exact keys used there).
- [ ] Record the internal-wall thickness of the segment (only the outer
      wall, 0.4 mm, was recorded in this session).
- [ ] Record the fiber material and diameter for the lizard-scale
      actuators (the inchworm paper used aramid fibers, E = 31 GPa —
      confirm the same fiber is used here).
