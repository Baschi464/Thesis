# Body-Tail Reconstruction Results and Gravity-Loaded Tip-Load Interpretation

## High-level intuitive explanation

The reconstruction results now give the paper a much stronger quantitative foundation. The body-tail actuator is no longer described only through photos or qualitative claims. Each representative posture has been converted into body and tail bending angles, curvatures, bending transmission ratio, front lifting height, and reconstruction error.

The S-shaped results are clean. Two top-view frames were analyzed, one for each crossed-channel actuation direction. In both cases, the body and tail curvatures have opposite signs, which is exactly what the S-shaped mode should produce. The first S-shaped frame at 11.1 kPa gave `theta_b = -104.9 deg`, `theta_t = 91.2 deg`, and `eta = 0.869`. The second S-shaped frame at 10.2 kPa gave `theta_b = 90.8 deg`, `theta_t = -92.9 deg`, and `eta = 1.023`. These two results are useful because they show that the crossed pneumatic routing works in both directions, not only in one favorable direction.

The reconstruction quality is also good. The RMS errors are all below approximately 0.24 mm for the S-shaped frames. This means the manually picked centerline points are well represented by circular arcs. For the paper, this is enough to support the two-segment constant-curvature model. The goal is not to predict the entire soft-body deformation from pressure; the goal is to show that the observed posture can be compactly represented by two constant-curvature arcs.

The U-shaped results are more nuanced and more interesting. Three side-view U-shaped frames were analyzed: no added tip load at 10.5 kPa, a 2.0 g tail-tip nut at 10.9 kPa, and a 5.7 g tail-tip nut at 11.4 kPa. All three frames satisfy the same-sign curvature condition expected for U-shaped bending. However, the shape and physical interpretation differ across the three loading conditions.

Without the added nut, the tail bends strongly while the body does not lift effectively. The body angle is `66.2 deg`, the tail angle is `157.4 deg`, and the bending ratio is `eta = 2.379`. The measured front height relative to the posterior hinge is `-0.7 mm`, so the selected front point is not actually lifted above the hinge reference. This is a useful baseline, but it is not a strong wall-transition posture.

With the 2.0 g nut, the body angle increases to `93.0 deg`, the tail angle becomes `66.8 deg`, and the front height reaches `7.2 mm`. This looks promising if we only look at the side-view number. However, the video and reconstruction image show that the tail also bent significantly out of the side-view plane. This is important and should not be hidden. The medium nut did not simply create an ideal counterweight-assisted U-shape. It exposed a torsion-bending coupled response.

The reason is mechanical. The intended U-shaped model assumes that the tail-tip mass stays in the vertical plane. In that case, the nut creates a useful counterweight moment for front lifting. But if the tail tip moves sideways by a lateral distance `y`, gravity creates an additional torsional moment about the body-tail axis. In 3D, for a tip position `r_tip = [x, y, z]^T` and gravity force `[0, 0, -mg]^T`, the moment is

```tex
\boldsymbol{\tau}_{\mathrm{tip}}
= \mathbf{r}_{\mathrm{tip}} \times \mathbf{F}_g
=
\begin{bmatrix}
-mgy \\
mgx \\
0
\end{bmatrix}.
```

The `mgx` component is the useful vertical-plane counterweight moment, while the `-mgy` component is the undesired torsional moment. If manufacturing error, chamber asymmetry, imperfect fiber placement, or nut misalignment causes a small sideways deviation, the nut weight can amplify that deviation. The actuator then bends and twists out of the intended vertical plane.

This explains why the 2.0 g nut is the problematic case. With no nut, the mass is too small to generate much torsional amplification. With the heaviest nut, the load is so large that the tail is more constrained and does not move enough for the sideways deformation to grow as much. The medium load is heavy enough to create torsion, but light enough that the tail can still move substantially. It therefore reveals the most visible out-of-plane instability.

With the 5.7 g nut, the body angle is `98.5 deg`, the tail angle is `63.1 deg`, and the front height reaches `11.1 mm`. The estimated gravitational moment about the posterior support is `1.51e-3 N m`, much larger than the `2.98e-4 N m` moment in the 2.0 g case and the `1.70e-5 N m` baseline value. This condition gives the largest projected front lifting height, but it should be described as a heavy-load projected U-bending condition rather than automatically as the best transition design. It increases useful projected lift, but it also changes the loading regime and may reduce mobility.

The best paper interpretation is therefore not simply "more weight is better." A more honest conclusion is that tail-tip mass is a design parameter that can improve projected front lifting, but it also increases sensitivity to out-of-plane misalignment. The counterweight idea is valid only if the added mass stays aligned with the intended vertical bending plane. Future designs should use an axisymmetric tail-tip weight, a better-centered attachment, improved chamber/fiber symmetry, or a lightweight guide to prevent torsional escape.

The table below summarizes the key extracted values.

| Mode | Load | Pressure | Body angle | Tail angle | Eta | Front height |
|---|---:|---:|---:|---:|---:|---:|
| S | none | 11.1 kPa | -104.9 deg | 91.2 deg | 0.869 | -- |
| S | none | 10.2 kPa | 90.8 deg | -92.9 deg | 1.023 | -- |
| U | none | 10.5 kPa | 66.2 deg | 157.4 deg | 2.379 | -0.7 mm |
| U | 2.0 g | 10.9 kPa | 93.0 deg | 66.8 deg | 0.718 | 7.2 mm |
| U | 5.7 g | 11.4 kPa | 98.5 deg | 63.1 deg | 0.641 | 11.1 mm |

## Implementation

1. Insert the LaTeX file `body_tail_reconstruction_results_section.tex` after the analytical model section, or merge it with the existing gravity-loaded U-bending section.

2. Copy the following figure files into the paper `figures/` folder, or edit the paths in the LaTeX file:
   - `Sbodydown11.1_reconstruction_overlay.png`
   - `Sbodyup10.2_reconstruction_overlay.png`
   - `Unonut10.5_reconstruction_overlay.png`
   - `Usmallnut10.9_reconstruction_overlay.png`
   - `Ubignut11.4_reconstruction_overlay.png`

3. Decide whether the heavy nut should be reported as `5.7 g` or `5.8 g`. The current reconstruction CSV and PDF figure use `5.7 g`, while earlier discussion sometimes used `5.8 g`. Use one value consistently in text, captions, tables, and plots.

4. In the paper, do not present the 2.0 g nut as a clean planar counterweight result. Describe it as a torsion-bending coupled response caused by out-of-plane deviation of the tail under tip loading.

5. If possible, extract a top-view or angled-view estimate of the out-of-plane tail displacement for the 2.0 g case. This would allow the torsional moment term `-mgy` to be quantified instead of only discussed qualitatively.

6. If there is time for a design improvement, replace the nut with an axisymmetric tail-tip weight or a better-centered load. This would make the counterweight experiment much cleaner.

7. For the final results figure, use one two-panel S-shaped reconstruction figure and one three-panel U-shaped reconstruction figure. Do not overload the figure with too many numerical annotations; keep the key values in the table.

8. Keep the reconstruction error values in the methods/results text or a supplementary table. The main paper only needs to state that the RMS fitting errors were below approximately 0.4 mm for all reconstructed frames.
