# Vertical U-bend load tests + wall-transition constraints (2026-07-06)

Type: experimental result + modeling constraints
Companion LaTeX: `2026-07-06_vertical-ubend-loads-wall-transition.tex`

## High-level explanation

This is the "can the body–tail lift things against gravity in the real
configuration" test. Assembled robot, legs on, posterior suction cups
stuck to the plate, body–tail curls up into a U carrying its own weight
plus the legs. Three conditions, pressures read off the CKD display in
the frames:

| Tip load | Pressure for U posture |
|---|---|
| none | 10.5 kPa |
| small nut, 2.0 g | 10.9 kPa |
| big nut, 5.7 g | 11.4 kPa |

The big nut ≈ the whole robot's mass (5.8 g), and it costs less than
1 kPa extra. That's the headline: at the nominal ~11 kPa operating point
the vertical mode still has real load margin. Tip heights / angles are
deliberately NOT quantified here — they belong to the image-based
reconstruction analysis (user decision).

**Two constraints the future model must respect** (this is why the
experiment was done this way):

1. **Gravity is not optional.** Unlike the FEM design studies (gravity
   neglected), here the actuator lifts its own weight + legs. Any
   constant-curvature or FEM reconstruction of the U mode must include a
   gravity load.
2. **The base is not free.** With the posterior cups attached, the
   central connector can only rotate about the axis through the two
   posterior legs — a constrained hinge, not a clamped or free base.
3. Gravity direction in the camera frame will come from a ChArUco board
   on the climbing surface + calibrated camera (calibration code already
   exists from earlier work).

## Implementation

- [ ] Fix figure paths (`figures/Unonut10_5.png`,
      `figures/Usmallnut10_9.png`, `figures/Ubignut11_4.png`) and
      uncomment.
- [ ] Reconstruction pipeline (future work, separate entries): extract
      tip height and body/tail angles per frame; correlate with displayed
      pressure; include gravity + posterior-hinge boundary condition;
      ChArUco pose estimation for gravity direction.
- [ ] Record whether the "U posture" criterion across the three loads was
      matched visually (same shape) or by another criterion — needed to
      interpret the pressure increments rigorously.
- [ ] Repetitions: single trials per load so far as captured — decide
      whether to repeat for dispersion before the paper.
