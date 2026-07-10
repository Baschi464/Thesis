# Lizard robot — system architecture (2026-07-06)

Type: design decision + numeric data
Companion LaTeX: `2026-07-06_lizard-robot-architecture.tex`

## High-level explanation

The lizard robot is the "assembled animal" built out of two actuator
families you already developed separately:

- **Body + tail**: two identical copies of the miniaturized three-chamber
  omnidirectional actuator (the same concept as the inchworm-paper
  actuator, scaled down 3x), joined end-to-end by a rigid central
  connector. They are pneumatically coupled through that connector, so one
  input line can drive both segments at once. Depending on which chamber
  path you pressurize, the pair deforms as an **S** (segments curve in
  opposite directions — useful for steering/undulation in the plane) or as
  a **U** (both curve the same way out of the plane — useful for lifting
  the front of the robot toward a wall).
- **Four legs**: single-chamber fiber-reinforced benders, one per corner,
  each ending in a suction-cup foot that is actively evacuated by the
  vacuum side of the pneumatic system.

Why this matters compared to prior gecko-like soft climbers (e.g. Schiller
2019): those use one planar-bending torso, so the body can only help in
the locomotion plane. Here the torso (body+tail) is omnidirectional and
split into two coupled segments, so the same hardware supports planar
steering *and* out-of-plane posture control for floor-to-wall transitions.

Key numbers (relaxed state, P = 0):

| Quantity | Value |
|---|---|
| Total mass (no tip loads) | 5.8 g |
| Body-tip to tail-tip | 85 mm |
| Across opposite legs + cups | 89 mm |
| Height | 8 mm |
| Legs | 4 |
| Body/tail actuator length (tube) | 33 mm (26 mm) |
| Body/tail outer diameter | 6 mm |
| Leg actuator length (tube) | 30 mm (24 mm) |
| Suction cup OD / vacuum height | 10 mm / 3 mm |

Operating regime: body-tail ~11 kPa → ~75° per segment; legs ~13 kPa →
~90°. The isolated small segment reaches ~180° at ~15 kPa, so the robot
runs well inside the actuator's envelope (safety margin against fiber
slip / seam rupture during repeated cycles).

Reference-mass context: comparable gecko-inspired soft climbers are
150–200 g; this robot is 5.8 g. Lower mass directly lowers the adhesion
force each suction cup must supply.

## Implementation

- [ ] Fix figure paths in the .tex (`figures/lizardExperimentSetup.jpeg`,
      `figures/Sbodydown11_1.png`, `figures/Sbodyup10_2.png`) and
      uncomment the `\includegraphics` lines.
- [ ] Replace `\cite{TODO-Baschiera-inchworm}` with the real BibTeX key of
      the inchworm paper once its year/venue entry exists in
      `references.bib`.
- [ ] Confirm the leg actuator outer diameter (not recorded in this
      session) and add it to Table `tab:lizard-global-specs`.
- [ ] Confirm whether the pneumatic control hardware is identical to the
      inchworm paper's 8-channel system (Arduino Mega 2560, 2V025-08
      valves, DP0110T-Y1 pumps) — stated as "same pneumatic system" in
      conversation but part-level identity not confirmed.
