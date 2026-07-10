# Per-actuator forward model: choosing a Gaussian Process

## The idea, informally

The AI controller for the planar gait works by "dreaming": for each of the
5 continuous actuators (4 legs + the body-tail unit, S-mode only for the
planar gait), we learn a small model that predicts how the actuator's
curvature will change (`Δz`) given its current curvature, the commanded
step, and which direction it was last moving in (that last part matters
because of backlash — the actuator behaves differently on the way up vs.
the way down). String five of these together and you can "imagine" what a
sequence of commands will do before running it on the real robot, and plan
around that imagination (MPPI / random shooting toward a target pose)
instead of learning a full policy network end-to-end.

The question this entry answers: what should that per-actuator model
*be*? Given how little data we'll have per actuator (tens to hundreds of
recorded transitions from single-actuator calibration), a Gaussian Process
was chosen over a neural network. Two flavors will be tried and compared
empirically: one with an analytical calibration curve as a prior and a GP
on the residual, and one with the GP predicting `Δz` directly (with a
plain least-squares fit as the floor, and a small MLP only as a fallback if
the GP clearly can't capture the nonlinearity).

### The geologist and the imprecise probe

This metaphor was developed and approved earlier in conversation, and also
motivates the (currently placeholder) figure for this entry.

You're a geologist mapping hidden bedrock under a plain. You can't see the
bedrock directly — only drill a few boreholes, each read with a shaky,
imprecise probe. Everywhere between boreholes is inference.

- **Only sees the datapoints** — the real bedrock exists everywhere, but
  you only get information at the holes you've actually drilled. Between
  them, there's only inference. This is exactly the situation with
  `(command → Δcurvature)` transitions: the GP only ever "sees" the
  recorded points.
- **Mean = best-estimate map** — asked "how deep is the bedrock here?",
  you blend the nearby boreholes, weighting closer ones more heavily. That
  blended surface is the GP mean.
- **Variance = confidence shading** — tight right on top of a borehole,
  wider between distant ones, and out past the last hole you fall back to
  your regional baseline guess while flagging that you're basically
  guessing. This is the single most useful property for this project: high
  GP variance during a planned rollout is a direct signal that the plan has
  wandered into territory the single-actuator calibration data never
  covered — most importantly, the loaded, closed-chain gait regime, which
  free-space calibration data simply doesn't sample.
- **Shaky probe = the noise term** — because each reading has its own
  error bar, you draw a surface that passes *near* the readings, not one
  that kinks to hit each one exactly. That's the GP's observation-noise
  term; it's why the mean doesn't interpolate noisy data exactly.
- **Kernel = your assumed rule for how bedrock varies between holes** —
  your prior belief about the geology's "character," before you've drilled
  anything.
- **Lengthscale = how far one borehole's information reaches** — long
  means gentle rolling terrain, one hole vouches for a wide area; short
  means broken terrain, and your confidence collapses just a few meters
  from any given hole. The command axis needs a short reach because of the
  deadzone — hence using a separate lengthscale per input dimension (ARD)
  rather than one shared lengthscale.
- **RBF vs. Matérn = the assumed *texture* of the bedrock** — RBF assumes
  glass-smooth, infinitely polished terrain, and will literally pave over
  a fault scarp (a sudden step) if one is there. Matérn assumes natural,
  weathered terrain, and can render the scarp instead of smoothing it away.
  Our scarp is the reversal deadzone / backlash — a near-step in the
  response right where the actuator changes direction — so Matérn (5/2 by
  default, 3/2 on the command axis if the deadzone turns out even sharper)
  is the better assumed geology here.

**Where the metaphor leaks:** the "nearby boreholes matter more" intuition
is a 2-D one. In higher-dimensional input spaces, "nearby" stops meaning
much — everything ends up far from everything else — which is exactly the
reason GPs degrade in high dimensions and neural nets take over there
instead. This project's state is low-dimensional (a handful of physical
variables per actuator), so the geologist intuition stays trustworthy here.

### Why a GP at all, and why not the thing everyone uses now

Neural networks dominate the field in general, but that's because the
field's dominant problems are large-scale and high-dimensional (millions
of examples, images/text where a fixed kernel means nothing and learned
features are essential) — exactly where GPs fail, both because of their
O(N³) training cost and because kernel-based "distance" stops being
meaningful in high dimensions. This project sits in the opposite corner:
a few hundred points per actuator, low-dimensional physical state, and a
task (planning/dreaming) where knowing "how much do I trust this
prediction" is directly useful, not just a nicety. That's the shrinking
niche where GPs are still the better tool. It's a statement about which
tool fits *this* data regime, not a claim that GPs are generally better.

### Kernel math (also in the .tex, repeated here for completeness)

- RBF: `k(r) = σ_f² exp(−r²/(2ℓ²))` — infinitely smooth, over-smooths the
  deadzone.
- Matérn-3/2: `k(r) = σ_f² (1 + √3 r/ℓ) exp(−√3 r/ℓ)` — once
  differentiable, tolerates a sharper transition.
- Matérn-5/2 (the default): `k(r) = σ_f² (1 + √5 r/ℓ + 5r²/(3ℓ²))
  exp(−√5 r/ℓ)` — twice differentiable, a middle ground.
- As ν → ∞, Matérn → RBF.
- GP posterior mean/variance: `μ(x*) = k*ᵀ(K+σ_n²I)⁻¹y`,
  `σ²(x*) = k** − k*ᵀ(K+σ_n²I)⁻¹k*`.

### The evaluation plan

Both variants (prior + GP-on-residual, and GP-on-Δz directly) get compared
on held-out one-step error, multi-step rollout error, how well-calibrated
the uncertainty actually is, and a data-efficiency curve (error vs. number
of training strokes seen). Whichever wins, *and* the comparison itself
(does the analytical prior actually help, or does the GP not need it?) is
a reportable result either way.

---

## Implementation

This is primarily a design decision with concrete downstream engineering
work once real single-actuator data exists. Nothing here can be
implemented against real data yet — no single-actuator command→curvature
transitions have been recorded on the robot as of this entry.

**What needs to be built, once the video-to-curvature extraction pipeline
and the per-actuator staircase recording protocol exist:**

1. **Data schema.** Log per-transition tuples `(z_t, u_t, dir_t, Δz)` per
   actuator, keeping the full stroke transient (not just the endpoint) so
   the deadzone/hysteresis branch is actually visible in the data, not
   just at the two extremes.
2. **Variant A (prior + residual GP).** Fit the steps→curvature staircase
   calibration `g_i` per actuator (try linear / zero-intercept quadratic /
   saturating, pick by held-out fit — same pattern as the existing
   pressure-angle calibration used elsewhere in this thesis, see
   `2026-07-07_body_tail_analytical_model.tex`, eq. (\ref{eqn:pressure_angle_fit})).
   pressure-angle calibration used elsewhere in this thesis, see
   `2026-07-07_body_tail_analytical_model.tex`, eq. `θ = aP² + bP`). Then
   fit a GP (Matérn-5/2 + ARD + white noise, via marginal-likelihood
   hyperparameter optimization — e.g. `scikit-learn`'s `GaussianProcessRegressor`
   or `GPyTorch` if exact inference at this data scale needs to stay fast)
   on the residual `Δz − Δz_prior`.
3. **Variant B (model-free GP).** Same GP setup, fit directly on `Δz` from
   `(z_t, u_t, dir_t)`. Implement the linear least-squares floor (B2)
   alongside it for comparison. Only build the small-MLP fallback (B3) if
   B/A clearly underfit a real nonlinearity — don't build it preemptively.
4. **Evaluation harness.** Held-out one-step error, multi-step rollout
   error (roll the learned model forward N steps from a held-out start and
   compare to the real recorded trajectory), a calibration check (does
   actual error fall within the predicted variance at the expected rate?),
   and a data-efficiency curve (retrain with increasing subsets of the
   training strokes, plot error vs. N).
5. **Composition.** Once all 5 per-actuator models exist, concatenate their
   predictions (plus the scripted suction-foot state) into the whole-robot
   forward model — no learned coupling term at this stage. Measure the gap
   between the composed model's rollout and real recorded gait trajectories
   as the transfer residual (a separate, already-planned study — not part
   of this entry's scope).
6. **Figure.** `figures/gp_geologist_metaphor.png` is currently a
   schematic built from synthetic toy data (see the `.tex` caption for the
   exact flag). Once real single-actuator transitions are recorded,
   regenerate this figure from the actual GP fit on real data — real
   bedrock/probe curves instead of synthetic ones, and a real deadzone in
   panel (b) instead of an illustrative step.
