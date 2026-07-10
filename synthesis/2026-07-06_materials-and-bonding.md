# Materials and bonding (2026-07-06)

Type: numeric data + design decision
Companion LaTeX: `2026-07-06_materials-and-bonding.tex`

## High-level explanation

Color code of the robot = material code:

- **Translucent/white = EcoFlex 00-30** (Smooth-On): all actuator tubes
  (body, tail, legs). Very soft, stretches a lot at low pressure — that's
  what lets the robot work at ~11 kPa. Yeoh coefficients used in the FEM
  work: C1 = 12.7 kPa, C2 = 423 Pa, C3 = −1.46 Pa.
- **Pink/reddish = Elastosil M4601** (Wacker): end caps, foot interfaces,
  suction cups. Much stiffer and tougher — parts that must hold shape,
  seal on fittings, and survive attach/release cycles.

Elastosil M4601 cured properties (from the Wacker datasheet, vulcanized
24 h at 23 °C): density 1.13 g/cm³ (ISO 2781), Shore A 28 (ISO 868),
tensile strength 6.5 N/mm² (ISO 37), elongation at break 700 % (ISO 37),
tear strength >30 N/mm (ASTM D 624 B), linear shrinkage <0.1 %, color
reddish brown. (Datasheet footnote: figures are a guide, not for
specifications.)

Curing and bonding recipe (as actually used):

| Step | Schedule |
|---|---|
| EcoFlex 00-30 cure | 90 °C, 90 min |
| Elastosil M4601 cure | 90 °C, 60 min |
| Elastosil↔EcoFlex bond (KE44-T adhesive) | 90 °C, 90 min |

## Implementation

- [ ] **Confirm KE44-T manufacturer**: written as Shin-Etsu Chemical in
      the .tex (moderate confidence — KE-44 is a Shin-Etsu RTV product
      line, but the manufacturer was not stated in the session). Verify
      against the actual tube/bottle.
- [ ] Fill the "n.r." cells for EcoFlex 00-30 (density, tensile,
      elongation, tear) from the Smooth-On datasheet — do NOT reuse the
      Elastosil ISO methods without checking Smooth-On's test methods
      (Smooth-On typically reports ASTM D412 etc.).
- [ ] Replace `\cite{TODO-Baschiera-inchworm}`.
- [ ] If the paper later includes a full FEM of the lizard-scale actuator,
      Elastosil M4601 Yeoh coefficients will be needed (not available —
      would require fitting from tensile data or literature search).
