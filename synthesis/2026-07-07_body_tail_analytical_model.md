# Body-Tail Analytical Model for the Lizard-Inspired Pneumatic Soft Robot

## High-level intuitive explanation

The analytical model should be understood as a reduced-order description of the body-tail deformation, not as a full physical simulation of the soft robot. The robot is made from fiber-reinforced silicone, internal pneumatic chambers, a rigid central connector, suction-cup feet, and tubing. A complete first-principles prediction from syringe motion to pressure field, wall strain, gravity-loaded deformation, contact constraints, and wall-transition success would require a much more complex model. That is not the goal here.

The goal is narrower and more defensible: use experimentally measured images to describe the dominant body-tail posture with a small number of meaningful variables. The body and tail are treated as two constant-curvature segments. This means each segment is approximated as an arc of a circle. The body has a measured bending angle `theta_b`, the tail has a measured bending angle `theta_t`, and their curvatures are computed as

```tex
\kappa_b = \frac{\theta_b}{L_b}, \qquad
\kappa_t = \frac{\theta_t}{L_t}.
```

Curvature is not the same thing as bending angle. Curvature is bending angle per unit length. The bending angle says how much the tangent rotates from the start to the end of a segment. The curvature says how concentrated that rotation is along the segment. If two segments bend by the same angle but one is shorter, the shorter one has larger curvature.

The main quantity used to compare body and tail bending is the bending transmission ratio

```tex
\eta_j = \frac{|\theta_{t,j}|}{|\theta_{b,j}|},
```

where `j` denotes the mode: S-shaped crossed-channel bending or U-shaped uncrossed-channel bending. If `eta_j < 1`, the tail bends less than the body. This is the safest primary metric because it comes directly from the measured deformation and does not require measuring internal pressure inside the body and tail.

The channel model is included only as an effective explanation. The narrow internal channels are sensitive to diameter because ideal laminar resistance scales as

```tex
R = \frac{8 \mu L}{\pi r^4}.
```

This explains why small differences in printed channels can strongly affect pneumatic transmission. However, the model should not claim a permanent static pressure drop across the connector. In a perfectly sealed pneumatic system at zero flow, a pure resistance would not maintain a pressure drop forever. Since the robot is driven by syringes rather than closed-loop pressure regulators, the more careful language is effective transmission, effective actuation, or bending transmission.

An optional pressure-based interpretation can be added using the isolated segment calibration. If the single-segment pressure-angle curve is fitted as

```tex
\theta = aP^2 + bP,
```

then a measured angle can be converted into an equivalent pressure using

```tex
P^{\mathrm{eff}} =
\frac{-b+\sqrt{b^2+4a\theta}}{2a}.
```

This allows an effective pressure transmission ratio

```tex
\gamma_j =
\frac{f^{-1}(|\theta_{t,j}|)}{f^{-1}(|\theta_{b,j}|)}.
```

This value should be treated as optional because it depends on the calibration curve. Under a nonlinear quadratic calibration, `eta_j` and `gamma_j` are not generally equal. They are equal only if the pressure-angle curve is linear through the origin.

The S-shaped horizontal model is the simpler case. It is measured in top view. Gravity acts mostly out of the image plane, so it is not included in the planar curvature reconstruction. The purpose of this experiment is to show that crossed channel routing creates opposite-sign body and tail curvatures, i.e.

```tex
\kappa_b \kappa_t < 0.
```

The U-shaped vertical model is different because gravity acts in the same plane as the deformation. The measured U-shape is therefore gravity-loaded. The measured angles should be written as

```tex
\theta_b^{\mathrm{meas}} = \theta_b^{\mathrm{pneu}} + \theta_b^g,
\qquad
\theta_t^{\mathrm{meas}} = \theta_t^{\mathrm{pneu}} + \theta_t^g.
```

The model does not try to solve the gravitational deformation separately. Instead, it reconstructs the measured gravity-loaded posture.

For wall-transition analysis, the posterior suction-cup feet impose an important boundary condition. When the posterior feet are attached to the substrate, the central connector cannot translate freely. It behaves approximately as if it rotates around the axis connecting the posterior legs. In side view, this axis is represented by a hinge point

```tex
\mathbf{p}_h = \frac{\mathbf{p}_L+\mathbf{p}_R}{2}.
```

The simplest constraint is

```tex
\mathbf{p}_c \simeq \mathbf{p}_h,
```

where `p_c` is the body-tail connector point. This is not a perfect mechanical joint, but it is a useful reduced-order representation of the suction-foot boundary condition.

The most important output of the U-shaped gravity-loaded model is front lifting height,

```tex
\Delta h_f = z_f-z_{f,0}.
```

This is more directly connected to wall transition than the bending angle alone. If the front tip lifts higher at the same pressure, the robot has a more favorable geometry for engaging the next surface.

The tail-tip weight experiment adds a design variable. A known mass at the tail tip applies a gravitational force

```tex
\mathbf{F}_{\mathrm{tip}} =
\begin{bmatrix}
0 \\
-m_{\mathrm{tip}}g
\end{bmatrix}.
```

The moment about the posterior hinge is

```tex
\tau_{\mathrm{tip}} =
(\mathbf{p}_{\mathrm{tip}}-\mathbf{p}_h) \times \mathbf{F}_{\mathrm{tip}}.
```

In 2D this becomes

```tex
\tau_{\mathrm{tip}} = -r_x m_{\mathrm{tip}}g,
```

where `r_x` is the horizontal distance from the hinge to the tail-tip mass. If the sign of this moment assists front lifting, the tail mass acts as a counterweight. The experiment should therefore compare front lifting height for the tested tip masses. In the current draft, the U-bending frames are reported for no added tip load, a 2.0 g nut, and a 5.7 g nut.

The tail mass can also shift the center of mass rearward. If the unloaded robot mass is `M_R`, the original longitudinal center of mass is `x_R`, and the tail mass is placed at `x_tip`, then

```tex
x_{\mathrm{CoM}}(m_{\mathrm{tip}})=
\frac{M_Rx_R+m_{\mathrm{tip}}x_{\mathrm{tip}}}
{M_R+m_{\mathrm{tip}}}.
```

The shift is

```tex
\Delta x_{\mathrm{CoM}} =
\frac{m_{\mathrm{tip}}(x_{\mathrm{tip}}-x_R)}
{M_R+m_{\mathrm{tip}}}.
```

This center-of-mass argument should be stated carefully. From the U-bending experiment alone, it is safe to say that the tail load modifies the gravity-loaded front lifting behavior and shifts the estimated center of mass rearward. It is stronger to claim improved transition stability only if wall-transition trials are also performed.

The final model figure should be simple and visually convincing. For the S-shaped mode, show a top-view frame with manually picked centerline points and the fitted two-arc reconstruction. For the U-shaped mode, show a side-view frame with the posterior hinge point, gravity direction, front lifting height, and fitted body-tail arcs. For the tip-load experiment, show either a plot of `Delta h_f` versus pressure for each mass, or a bar plot of maximum front lifting height for each mass.

## Implementation

1. Insert the LaTeX section `body_tail_analytical_model.tex` after the current pneumatic coupling section or before the experimental bending-characterization sections.

2. Add `\usepackage{amsmath}` to the paper preamble if it is not already present.

3. Replace or merge the current short effective pressure-transmission paragraph with the more careful model wording. Avoid claiming a permanent static pressure drop between body and tail.

4. For each S-shaped and U-shaped reconstruction frame, extract:
   - pressure from the display,
   - body centerline points,
   - tail centerline points,
   - body bending angle,
   - tail bending angle,
   - body and tail curvature,
   - bending transmission ratio,
   - reconstruction RMSE.

5. For each U-shaped gravity-loaded frame, additionally extract:
   - posterior left and right suction-foot positions,
   - posterior hinge point,
   - connector point,
   - front-tip position,
   - tail-tip position,
   - front lifting height,
   - gravity direction from the ChArUco board or vertical reference.

6. For each tail-tip load case, compute:
   - `Delta h_f`,
   - maximum front lifting height,
   - tail-tip moment about the posterior hinge,
   - optional center-of-mass shift.

7. Prepare final figures:
   - S-shape reconstruction overlay: picked points and fitted two-arc model.
   - U-shape reconstruction overlay: hinge point, gravity arrow, front height, fitted arcs.
   - Tip-load result: front height versus pressure or maximum front height versus tip mass.

8. If the actual heavy nut mass is 5.8 g rather than 5.7 g, update the value consistently in the LaTeX, Markdown, figure caption, and data table.
