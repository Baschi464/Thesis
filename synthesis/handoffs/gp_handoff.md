# Handoff for `thesis-sync` (run this in Claude Code)

**To the Claude Code session reading this:** this is a curated briefing prepared in a separate Claude.ai chat (which had no GitHub write access). Please run the **`thesis-sync`** skill on the content below. Follow the skill's normal procedure — in particular, **do the Step 2 duplicate check against `synthesis/INDEX.md` yourself** (the originating chat could not reach the repo). The originating chat believes this is a **NEW entry** (nothing about the GP forward model / kernel choice / this metaphor has been synced before), but verify against `INDEX.md` before writing, per the skill.

**Entry type:** primarily a **design decision** (choice of forward-model architecture for the AI-controller milestone) plus a **theoretical/explanatory** component (what a GP is and why it fits). Follow the skill's mapping: Methods/Design subsection for the decision, short model/discussion subsection for the explanation.

**Figure:** a figure was generated for this entry — `gp_geologist_metaphor.png` (and `.pdf`). Place it in `figures/` before running the skill so the skill's Step 5 filename-overlap check finds it. **IMPORTANT — flag this in the synthesis (both the .tex caption and the .md):** this figure is currently **schematic/illustrative only, generated from synthetic toy data**. Add an explicit note that *once real single-actuator data is recorded on the lizard robot, an equivalent figure should be regenerated from the actual measured `(command → Δcurvature)` data* — i.e., replace the toy bedrock/probe curves with real GP fits on real transitions. Mark the current figure as a placeholder to that effect.

**Scope / splitting:** the **GP explanation + architecture decision** is the primary entry. There is a **"Related forward-model decisions" appendix** at the end (hysteresis feature, evaluation protocol, augmentation policy). Treat that as either part of this entry or a **second related synthesis entry** — your judgment per the skill; it is closely related but arguably distinct.

**Do not fabricate:** if a citation is needed and unavailable, use `\cite{TODO-...}` per the skill/style-guide rule. Several sources below are arXiv preprints whose peer-review status is unverified — flag as needed.

---

## PROJECT CONTEXT (minimal, for placing the entry correctly)

The thesis milestone this belongs to: building an **AI controller that reproduces a planar forward gait** on the pneumatically-actuated, lizard/gecko-inspired soft climbing robot. The controller approach is **latent-space prediction** ("dreaming"): learn per-actuator **forward models** in a compact curvature-latent state, compose them, and use them to predict/plan the gait.

Key established facts this entry depends on:
- **5 continuous actuators** modeled: 4 legs + 1 body–tail (body–tail = one coupled unit; S-mode only for planar gait; ch5/ch6 alternate, never co-actuated).
- **State/latent `z`** = per-actuator constant-curvature (PCC) parameters (κ or bending angle θ in the actuator body frame), extracted from overhead video of colored actuator stripes, homography-rectified to the ~8 mm actuator plane. Suction feet = scripted binary state, not modeled dynamically.
- **Control input `u`** = commanded stepper position / displaced volume per channel (open-loop; **no pressure sensing, no closed-loop pressure control**). Video curvature is the only ground-truth state.
- **Forward model** target = **Δz** (one-step curvature change), input = `(z_t, u_t, dir_t)` where `dir_t` = last-command-direction (hysteresis/backlash branch indicator).
- Data is **small** (single-actuator recordings, tens–hundreds of transitions per actuator). This scale is the central driver of the architecture choice below.

---

## PRIMARY CONTENT TO SYNC — Gaussian Process forward model

### The decision
Use a **Gaussian Process (GP)** as the per-actuator forward model, in two variants to be compared empirically:
- **Variant A (prior-based):** an *empirical* steps→curvature calibration `g_i` (fitted from the actuator's own staircase data — linear / zero-intercept quadratic / saturating, best by held-out fit) as an analytical prior, **plus a GP on the residual** `Δz − Δz_prior`.
- **Variant B (model-free):** **GP directly on Δz**, no prior. With a **linear least-squares baseline** (B2) as the floor, and an optional small **MLP** (B3) only if a strong nonlinearity defeats the GP.

Pick the winner from held-out one-step error, multi-step rollout error, **uncertainty calibration**, and **data-efficiency curves** (error vs. number of training strokes). The prior-vs-model-free comparison is itself a legitimate result.

### Why a GP (the reasoning, for the discussion subsection)
- **Small-data regime:** GPs are strong with tens–hundreds of points; the model is essentially the data + a smoothness assumption, so almost nothing to overfit. An MLP would overfit at this scale without heavy regularization.
- **Calibrated uncertainty for free:** every prediction carries a variance that is small near training data and **grows away from it**. This is the key property for "dreaming"/planning: it flags when a rollout enters a region the data never covered — e.g., the **loaded, closed-chain gait regime** that free-space single-actuator data does not cover. High GP variance in gait regions is itself evidence of the coverage gap (this ties into the separately-planned open-chain→closed-chain transfer-residual study).
- **Cost is a non-issue at this scale:** GP training is O(N³) time / O(N²) memory — prohibitive at N=10⁶ but trivial at N=few-hundred.
- **Why MLPs dominate the field generally but not here:** MLPs win at *scale* (native to millions of examples) and at *high-dimensional / structured inputs* (images, text) where a fixed distance-kernel is meaningless and learned features are essential. Those are exactly the regimes where GPs fail (O(N³) infeasible; curse of dimensionality). This project sits in the opposite corner — low-dimensional physical state, few hundred points, uncertainty matters — the shrinking niche where GPs remain the better tool. Popularity tracks the dominant problem type, not universal superiority.

### Kernel choice
- **Default: Matérn-5/2 with ARD** (a separate lengthscale per input dimension) + a WhiteKernel noise term. Standardize inputs.
- Rationale: the **RBF (squared-exponential)** kernel assumes an *infinitely smooth* function and will **over-smooth genuine sharp features**. Our system has one — the **reversal deadzone / backlash** (a near-step in the response). **Matérn** (5/2, or 3/2 on the command axis if the deadzone is sharp) tolerates sharper transitions. ARD lets the command dimension use a shorter lengthscale (rougher) than the smooth state dimensions.
- Kernel math for the .tex:
  - RBF: `k(r) = σ_f² exp(−r²/(2ℓ²))` — infinitely differentiable.
  - Matérn-3/2: `k(r) = σ_f² (1 + √3 r/ℓ) exp(−√3 r/ℓ)` — once differentiable.
  - Matérn-5/2: `k(r) = σ_f² (1 + √5 r/ℓ + 5r²/(3ℓ²)) exp(−√5 r/ℓ)` — twice differentiable.
  - Matérn → RBF as ν→∞.
- Hyperparameters (ℓ, σ_f², σ_n²) fit by maximizing the marginal likelihood (not hand-tuned).
- The `dir_t` feature places loading/unloading branches in different input regions so the GP does not average across the deadzone discontinuity.

### GP posterior equations (for the .tex)
With training inputs X, outputs y (= Δz), test input x*, kernel matrix K, test–train vector k*, self term k**, noise σ_n²:
- Mean: `μ(x*) = k*ᵀ (K + σ_n² I)⁻¹ y`
- Variance: `σ²(x*) = k** − k*ᵀ (K + σ_n² I)⁻¹ k*`
Mean = kernel-weighted blend of training outputs; variance shrinks near data, grows far from it, reverting to the prior mean far away.

---

## THE METAPHOR (approved in-chat — use it in the .md intuitive section)

> **This metaphor was actually developed and approved in the originating conversation**, so per the skill it may be used in the .md high-level section. It also motivates the figure.

**The geologist and the imprecise probe.** You are a geologist mapping the **hidden bedrock height** under a plain. You cannot see the bedrock — only **drill a few boreholes**, each measured with a **shaky probe** (imprecise: readings have error bars). Everywhere else is inference.

- **"Only sees the datapoints":** the true bedrock exists everywhere but is accessible only at the boreholes; between them there is only inference. (= regression sees only the recorded `(input → Δz)` points.)
- **Mean = the best-estimate map:** asked the depth *here*, the geologist blends nearby boreholes, weighting closer ones more. That blended surface is the GP mean.
- **Variance = confidence shading:** tight on top of a borehole, wider between distant ones, and far from every hole the geologist falls back to the regional baseline while flagging maximum uncertainty. (= GP variance small near data, ballooning far away, reverting to prior. This is the signal that flags rollouts entering uncovered gait regimes.)
- **Shaky probe = the noise term:** because the probe is imprecise, the geologist draws a surface passing *near* the readings, not kinking to hit each exactly. (= observation noise σ_n²; the mean does not interpolate noisy points exactly.)
- **Kernel = assumed rule for how bedrock varies between holes:** the prior belief about the geology's character before drilling.
- **Lengthscale = how far one borehole's information reaches:** long = gentle folds, one hole vouches for a wide area; short = broken terrain, uncertainty balloons metres away. (The command axis, with its deadzone, needs a short reach — hence ARD.)
- **RBF vs Matérn = assumed *texture* of the bedrock:** RBF assumes **glass-smooth, polished** terrain and will **pave over a fault scarp** (a sudden step); Matérn assumes **natural, weathered** terrain and can **render the scarp**. Our "scarp" is the reversal deadzone — so Matérn is the better assumed geology. (ν dials roughness: 1/2 craggy → 5/2 rolling hills → ∞ = RBF's glass.)

**Where the metaphor leaks (include as a caveat):** 2-D "distance" is honest intuition, but in higher-dimensional input space "nearby" weakens (everything drifts far from everything) — the same reason GPs fade exactly where neural nets take over. This project's state is low-dimensional, so the geologist stays trustworthy.

---

## FIGURE NOTES (for the .tex caption and .md)

`gp_geologist_metaphor.png/pdf` — two panels:
- **A:** hidden bedrock inferred from a few imprecise probes (error bars); GP mean passing near not through them; confidence band tight over boreholes, ballooning in the right-hand data gap where it reverts to baseline.
- **B:** RBF vs Matérn at a "scarp" (deadzone) — RBF over-smooths the step, Matérn follows it.

**REQUIRED FLAG (do not omit):** state clearly that this figure is **schematic, generated from synthetic toy data for illustration only**, and that **once real single-actuator data is recorded on the lizard robot, an equivalent figure must be regenerated from the actual measured `(command → Δcurvature)` transitions** (real GP fits, real deadzone, real uncertainty band) to replace this placeholder.

---

## APPENDIX — Related forward-model decisions (may be split into a second synthesis entry)

- **Composition is structural, not learned:** the whole-robot forward model concatenates the 5 per-actuator predictions + scripted suction; the coupling correction is **not** modeled — the mismatch vs. recorded gait is measured as the transfer residual (separate planned study). A learned coupling term on gait data is a stretch goal only.
- **Controller is not a learned network:** either open-loop replay of the recorded gait, or **sampling-based planning (MPPI / random shooting)** over the composed model toward goal keyframes. No learned policy π (data-hungry; avoided).
- **Hysteresis / deadzone:** collect an ascending/descending staircase; log full stroke transients (not just endpoints); include `dir_t`. Validate that the model reproduces the loading/unloading gap.
- **Augmentation policy (honest, narrow):** use only truth-injecting augmentation — measured-noise input jitter (noise level from vision-pipeline centroid/fit-error measurements) and using all held-still frames. **Exclude** VAE/autoencoder-noise sampling and hand-interpolation of transitions (add no dynamical information; feeding a model's own interpolations back **falsely shrinks GP uncertainty / corrupts calibration**). Augmentation improves precision/robustness, **never coverage** — the binding constraint is coverage (free-space vs. loaded-gait), which only real near-gait data or a physics model closes.
- **Gait data = target + evaluation only**, never forward-model training data, never augmented.

---

## SOURCES (from the originating chat; verify before citing — several are preprints)
- V-JEPA 2 (Assran et al., 2025, arXiv:2506.09985) — action-conditioned latent world model; defines the JEPA representation objective. **Note terminology:** our forward model is a **Dreamer-style supervised latent dynamics model**, NOT a JEPA (JEPA = representation-learning objective with stop-gradient EMA target encoder). Use "JEPA-inspired (latent-space prediction)" only.
- "Learning to Crawl: Latent Model-Based RL for Soft Robotic Adaptive Locomotion" (arXiv:2510.05957, 2025) — closest prior work (latent dynamics model for soft-crawler gait).
- "Dynamic Modeling and MPC for Locomotion of Tendon-Driven Soft Quadruped" (arXiv:2602.16371, 2026) — modular per-leg composition onto a torso.
- Rasmussen & Williams, *Gaussian Processes for Machine Learning* (2006) — standard GP reference for kernels / posterior / marginal likelihood (use for the GP math citations).

---

## INSTRUCTIONS RECAP for the Claude Code session
1. Run `thesis-sync`. Do the **duplicate check against `synthesis/INDEX.md`** first (originating chat believes NEW, but verify).
2. Read `references/style-guide.md` + `templates/ieee_section_template.tex`; match the user's `ieeeconf` style. Use `\cite{TODO-...}` for anything unverifiable.
3. Write the `.tex` (Methods/Design decision + short discussion for the GP explanation) and the `.md` (intuitive geologist-metaphor section first, then implementation).
4. Use `gp_geologist_metaphor.png` from `figures/` and **add the placeholder/regenerate-with-real-data flag** in both caption and .md.
5. Decide whether the appendix is part of this entry or a second related entry.
6. Update `INDEX.md`; commit and push; tell the user what was committed.
