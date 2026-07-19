# Inchworm actuator — geometry, FEM optimization, energy model

The whole robot lives or dies on one number: how much pressure it takes to
bend the actuator to the angle a stride needs. Lower pressure means smaller
pumps, less energy per step, and less stress on the silicone seams. So the
design work here is essentially a pressure-minimization problem, done in
COMSOL before anything was cast.

**Why bending, not volume.** The energy per gait cycle (Eq. energy) is
pressure × volume summed over the bend, elongation, and vacuum phases. You
could lower energy by shrinking chamber volume, but volume is capped by what
the mold can physically produce. Pressure, on the other hand, is a design
knob — so the optimization targets "least pressure for 180° of bend."

**The geometry.** A cylinder with three 120° pie-slice chambers meeting at
the center. Pressurize one → bends toward it; two → bends between them;
all three → elongates. Radial symmetry is what makes bending work in any
direction while keeping the peak material strain down.

**What the FEM said.** Two parameters dominate: thinner outer wall and
tighter fiber spacing both drop the required pressure a lot. The
counter-intuitive result is about "ballooning" — the tendency of the
pressurized chamber to bulge sideways instead of bending the whole actuator.
Normally you'd fight ballooning (stiffer inner walls, radial fibers). Here,
fighting it did **not** help, because in a three-chamber actuator the two
*un*pressurized chambers already act as a strain-limiting spine — they do the
job that anti-ballooning reinforcement would, for free. That is a genuine
design insight and it's why the final actuator stays simple (single silicone,
circumferential fibers only).

Materials in the model: EcoFlex 00-30 body (Yeoh hyperelastic), optional
EcoFlex 00-50 inner walls, aramid fibers and PEI caps as linear-elastic. The
bending angle is read off two opposed tip points via a simple arctangent
(Eq. bending), with the base clamped vertical.

## Implementation

Add to the `main.tex` preamble: `\usepackage{multirow}` and
`\usepackage{makecell}` (the materials table needs both). Figures already
staged: `figures/actuatorSTL.eps`, `figures/crossSection.eps`,
`figures/comsol.eps`. No modeling work is outstanding — the FEM campaign is
complete and its optimized parameters (minimal wall thickness, minimal fiber
spacing, no anti-ballooning reinforcement) are what the fabricated actuator
in the next entry uses.
