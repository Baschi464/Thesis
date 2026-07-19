# Inchworm robot — introduction and gait concept

This is the opening of the inchworm-robot block, which is prior work that the
lizard robot builds on. The inchworm is the simplest version of the whole
research line: one soft actuator, two suction-cup feet, and nothing else. It
exists to prove one idea — that a single omnidirectional bending actuator can
both crawl forward *and* steer *and* climb from a floor onto a wall, without
needing separate parts for each job.

The trick is the actuator's cross-section: one cylinder split into three
pie-slice chambers at 120° each. Pressurize one chamber and it bends toward
that side; pressurize two and it bends in the direction between them;
pressurize all three and it just gets longer. So the same part gives you
bending in any direction (omnidirectional) plus elongation. That is what lets
a single actuator do everything.

Locomotion is an inchworm cycle in four phases, but with a twist versus a
classic inchworm. A classic inchworm only contracts and extends along one
line. This one **bends** to reel the back foot forward, then **elongates** to
push the front foot ahead — so bending and elongation are coupled into the
stride. The two feet are suction cups, and they take turns anchoring: front
foot stuck while the back foot moves, then back foot stuck while the front
moves. A small detail that matters a lot: each foot is joined to the actuator
tip through a soft "hinge" of silicone, so that when the actuator bends the
foot can passively rotate and stay flat on the surface instead of peeling
off. Without that hinge the suction breaks during phases 1 and 3.

Everything downstream in this block — the FEM optimization of the chamber
geometry, the fabrication, the 8-channel pneumatic box, the sliding-mode
controller, the GUI, and the forward/steering/transition gaits — is in
service of making this one-actuator concept actually work on a 60° incline.

## Implementation

No further implementation needed — this entry is descriptive/foundational and
reproduces the published concept. Cross-references to resolve once the block
is wired into `main.tex`: `\ref{sec:lizard-architecture}` (the lizard chapter
that this actuator was later miniaturized into) and
`\ref{sec:inchworm-pneumatics}` (the pneumatic-system section in this block).
Figure used: `figures/concept.eps` (already staged).
