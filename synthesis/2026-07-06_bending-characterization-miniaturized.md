# Bending characterization of the miniaturized segment (2026-07-06)

Type: experimental result
Companion LaTeX: `2026-07-06_bending-characterization-miniaturized.tex`

## High-level explanation

Same rig as the inchworm paper: actuator hangs from an upside-down clamp,
one chamber is inflated with a hand syringe through an in-line CKD PPX
pressure display, a camera records, angles are read optically. The
actuator bends *against gravity*.

Two results:

**1. Shrinking 3x barely costs anything.** Full-scale segment (bendable
length L = 60 mm) vs mini (L = 20 mm): same curve shape (soft start, then
steep rise past ~8–10 kPa). The mini needs modestly more pressure for the
same angle — endpoints read from the plots: mini ~173° @ 16.4 kPa vs
full-scale ~182° @ 14.8 kPa. So a 3× miniaturization keeps the full
functional bending range at a slightly higher working pressure.
(Note on "L": it's the *bendable* length — the tube minus the parts held
by caps/connectors. Mini tube = 26 mm, of which 20 mm bendable.)

**2. The central fiber pays off exactly where the robot operates and
above.** With vs without central axial fiber: identical below ~9 kPa;
above that, the central-fiber version climbs faster — ~180° @ 15.0 kPa vs
~173° @ 16.4 kPa without. Interpretation (consistent with design intent,
stated as such): the fiber blocks axial stretch of the neutral axis, so
at high pressure inflation goes into curvature instead of elongation.

**Scope guard (important, user-specified):** 180° @ 15 kPa is the
*isolated single-segment characterization only*. The assembled robot runs
the coupled body–tail at ~11 kPa → ~75° per segment. Never attribute the
180° figure to the robot in operation.

## Implementation

- [ ] Fix figure paths (`figures/experimentalsetup.png`,
      `figures/3xSizevsMini.png`, `figures/centralFiberGraph.png`,
      `figures/centralfiberbendingexperiment.png`) and uncomment.
- [ ] **Confirm**: is the 3x (L=60 mm) curve the actuator of the inchworm
      paper itself, or a separately built 3x specimen? The .tex currently
      says the setup is the inchworm paper's; the identity of the 3x
      specimen should be stated precisely.
- [ ] **Confirm**: in the size-comparison plot, is the 1x curve the
      configuration WITHOUT the central fiber? Its endpoint (~173° @
      16.4 kPa) matches the "w/o central fiber" curve exactly, suggesting
      the same dataset. If so, say so in the caption; if the robot's
      actual configuration (with fiber) differs, the comparison text
      should note it.
- [ ] Number of repetitions / error bars: the plots show single curves.
      If the experiments were repeated, add n and dispersion; if not,
      state single-trial explicitly in the paper (reviewers will ask).
- [ ] Inflation vs deflation hysteresis was shown for the full-scale
      actuator in the inchworm paper; not captured for the mini — decide
      whether to measure it.
