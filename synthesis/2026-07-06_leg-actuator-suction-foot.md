# Leg actuators + suction-cup feet (2026-07-06)

Type: design decision + numeric data
Companion LaTeX: `2026-07-06_leg-actuator-suction-foot.tex`

## High-level explanation

The legs are deliberately simpler than the body/tail. A leg only needs
one motion — lift the foot, plant the foot — so it's a **single-chamber**
bender, not a three-chamber one. Design:

- Silicone tube 24 mm (30 mm total actuator length).
- **Double-helical fiber** wrapped at ~25° average pitch angle: stops the
  tube from ballooning radially but lets it strain axially.
- **One longitudinal fiber on one side**: that side can't stretch, the
  opposite side can, so pressurizing the chamber bends the leg toward the
  fiber. Same "inextensible layer" trick as strain-limiting layers in
  pneu-net actuators, done with a single thread.
- Performance in the robot: ~90° bend at 13 kPa.

The **foot** is a suction cup cast in Elastosil M4601 (the pink parts):
10 mm outer diameter, 3 mm internal vacuum height. Cups are **actively
evacuated** — a vacuum channel from the same pneumatic system, one per
foot — so attach/release is commanded at the right gait phase. Each leg
therefore has two ports: pressure (bending) and vacuum (foot).

## Implementation

- [ ] Fix figure path (`figures/lizardleg.jpeg`) and uncomment.
- [ ] Record the leg tube outer diameter and wall thickness (not captured
      in this session).
- [ ] Verify the BibTeX key for the fiber-reinforced-bending-finger
      reference (`Mao2020SoftFiber` per the inchworm paper's list) —
      check it matches the key in `references.bib`.
- [ ] Note for future measurement: suction-cup adhesion force on the
      acrylic substrate (normal and shear) is not yet measured; needed if
      the paper claims climbing margins.
- [ ] Design-rationale claim intentionally kept minimal in the .tex: the
      only stated reason for active evacuation is gait-phase-commanded
      attach/release. If additional rationale (e.g. low normal force at
      5.8 g body weight) should be claimed, confirm it explicitly first.
