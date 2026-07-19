# Inchworm robot — locomotion performance (forward, steering, transition)

This is the payoff: does the one-actuator concept actually move on a real 60°
slope? Three gaits were demonstrated, all built from the same four-phase
inchworm cycle, differing only in what happens during the bending phase.

**Forward gait (4 phases).** Anchor the front foot, bend to reel the back foot
up (a small puff of pressure first pops the back cup loose), then swap anchors
— front foot loose, back foot stuck — and finally inflate all three chambers
to straighten out and shoot the front foot forward. Bend to gather, elongate
to reach. Repeat.

**Steering gait.** Identical to forward *except* in the bending phase you
pressurize the top chamber **plus one side chamber**. That tilts the bend
off-axis, so instead of reeling straight forward the robot pulls in slightly
sideways — about **16° of turn per full cycle**. Same hardware, one extra
chamber energized.

**Floor-to-wall transition (15 steps).** This is the trick no flat-plane
inchworm can do. Bend sideways (one side chamber) to swing the loose front
foot around the corner edge; then bend *upward* (both side chambers) to lift
that foot up and plant it on the wall; once it's anchored on the incline, just
run the normal forward gait to walk the back half of the body up after it. The
omnidirectional actuator is what makes the "reach around and up over an edge"
move possible.

**Why it matters for the thesis.** This chapter is the foundation the rest of
the thesis stands on. The three-chamber omnidirectional actuator and the
multichannel pneumatic control proven here are exactly what get miniaturized
and reused in the lizard robot — so the forward/steering/transition
demonstrations here justify carrying that actuator concept forward.

## Implementation

No further implementation needed for the write-up — the gaits were
demonstrated and are captured in the performance figure
(`figures/performance.eps`, staged; a raster `performance.png` is also staged
as a fallback). Open item from the paper itself: the "Gait Experimental
Verification" subsection was marked TODO (quantitative gait metrics — speed,
step length, repeatability). If/when that experiment is run, it becomes its
own results entry rather than a change to this one.
