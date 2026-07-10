# Fabrication: mold, capillary demolding, fiber wrapping (2026-07-06)

Type: design decision (fabrication process)
Companion LaTeX: `2026-07-06_fabrication-molding-process.tex`

## High-level explanation

The hard part of making the miniaturized three-chamber segment is that
everything is tiny: 6 mm tube, 0.4 mm outer wall, three internal chambers.

**Mold** (see `threechambermold.png` labels):
- three **120° fan-shaped chamber cores in brass** → form the chambers and
  the internal walls;
- **acrylic cover** halves with a semicylindrical groove → form the outer
  tube surface;
- **0.5 mm acrylic spacers** with a three-lobed cutout → hold the brass
  cores centered and angularly aligned at both ends.

**Demolding trick (the actual invention of this entry):** pulling the
brass fans out of a cured 0.4 mm wall tears the silicone. Solution: wet a
tweezer tip with **ethanol**, slide it between brass and silicone, and
capillary action pulls the ethanol along the whole interface, acting as a
temporary release agent. The cores then slide out cleanly; the ethanol
evaporates.

**Fibers:** dip the demolded tube in fresh (uncured) silicone, wind the
circumferential loops by hand, scrape the excess silicone off each fiber
with tweezers → ~1.5 mm average spacing (manual process, hence
"average"). Central axial fiber goes through the wall junction; the legs'
longitudinal fiber goes along one side. Caps/feet are cast separately in
Elastosil M4601 and glued on (KE44-T, 90 °C / 90 min).

## Implementation

- [ ] Fix figure path (`figures/threechambermold.png`) and uncomment.
- [ ] Clarify the geometric relation between the 0.5 mm spacer thickness
      and the 0.4 mm cast wall thickness (the .tex deliberately does NOT
      claim the spacer sets the wall thickness, because 0.5 ≠ 0.4 —
      explain how the 0.4 mm wall is actually obtained).
- [ ] Record how the leg (single-chamber) tube is molded — same mold
      family with a cylindrical core instead of fans? Not captured.
- [ ] Record whether the central connector is 3D printed and in what
      material (its CAD exists; fabrication route not captured).
- [ ] If a fabrication figure panel is wanted for the paper, consider a
      photo sequence of the ethanol-release step — currently only the CAD
      of the mold exists as a figure.
