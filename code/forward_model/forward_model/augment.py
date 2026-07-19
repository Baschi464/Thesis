"""
augment.py -- narrow, honest augmentation (gp_code_handoff.md SS7).

Implemented:
  - A-1 measured-noise input jitter (`jitter_z`), OFF by default: perturbs
    z_t by Gaussian noise at the DATA'S OWN meas_noise_sd (not invented),
    target dZ unchanged. Toggle in evaluate.py runs to A/B test whether it
    helps.
  - A-2 held-frame grouping (`group_held_frames`), ON by default: averages
    contiguous held-still frames at the same setpoint into fewer,
    higher-SNR rows. Pure noise reduction, no new dynamical information.
  - A-3 mirror-symmetry (`mirror_symmetry_augment`), optional + WARNED,
    default OFF: treats one leg's transitions as a weak initializer for a
    nominally-mirrored leg. Emits a warning every call: this conflicts
    with the per-actuator manufacturing-variability premise the rest of
    this package assumes (each actuator gets its own fitted model because
    real actuators are NOT identical).

Explicitly NOT implemented (gp_code_handoff.md SS7): VAE/autoencoder-noise
sampling and hand-interpolation of transitions. Both add zero new
dynamical information -- they resample/interpolate what's already in the
data -- and feeding a model's own interpolated points back as if they were
observations FALSELY SHRINKS GP predictive uncertainty (the interpolated
points sit suspiciously close to the GP's own mean, so training on them
makes the posterior overconfident exactly where it should stay honest
about the coverage gap). Coverage (free-space vs. loaded-gait), not
augmentation, is the binding constraint here, and only real near-gait data
or a physics model closes it (gp_handoff.md appendix).
"""

import warnings

import numpy as np
import pandas as pd


def jitter_z(X: np.ndarray, meas_noise_sd, jitter_scale: float = 1.0,
             n_state_dims: int = 1, rng=None) -> np.ndarray:
    """A-1: return a COPY of X with z_t (first n_state_dims columns)
    perturbed by N(0, (meas_noise_sd*jitter_scale)^2). u_t/dir_t columns
    are left untouched -- jittering u would need its own noise measure
    (step-count uncertainty), which isn't defined/measured, so it's
    deliberately out of scope here (do not invent a number for it).
    """
    rng = rng or np.random.default_rng(0)
    X = np.asarray(X, dtype=float).copy()
    sd = np.broadcast_to(np.asarray(meas_noise_sd, dtype=float) * jitter_scale, (len(X),)).reshape(-1, 1)
    noise = rng.normal(0.0, 1.0, size=(len(X), n_state_dims)) * sd
    X[:, :n_state_dims] += noise
    return X


def group_held_frames(df: pd.DataFrame, tol: float = 1e-6) -> pd.DataFrame:
    """A-2: within each stroke, average contiguous held-still runs (frames
    where |dkappa| <= tol at a constant u_t -- already near steady state)
    into one representative row (mean kappa_t/kappa_tp1, summed dt).
    Transient (still-moving) frames are left as individual rows. Requires
    stroke_id (see data.py::load_transitions, which infers it if absent).
    """
    if df.empty:
        return df.copy()

    out_rows = []
    for _, g in df.groupby("stroke_id", sort=False):
        g = g.sort_values("t_host").reset_index(drop=True)
        i, n = 0, len(g)
        while i < n:
            if abs(g.loc[i, "dkappa"]) <= tol:
                j = i
                while (j < n and abs(g.loc[j, "dkappa"]) <= tol
                       and g.loc[j, "u_t"] == g.loc[i, "u_t"]):
                    j += 1
                block = g.loc[i:j - 1]
                row = block.iloc[-1].copy()
                row["kappa_t"] = block["kappa_t"].mean()
                row["kappa_tp1"] = block["kappa_tp1"].mean()
                row["dkappa"] = row["kappa_tp1"] - row["kappa_t"]
                row["dt"] = block["dt"].sum()
                row["quality"] = block["quality"].mean()
                if "kappa_t_true" in block.columns:
                    row["kappa_t_true"] = block["kappa_t_true"].mean()
                    row["kappa_tp1_true"] = block["kappa_tp1_true"].mean()
                out_rows.append(row)
                i = j
            else:
                out_rows.append(g.loc[i].copy())
                i += 1

    return pd.DataFrame(out_rows).reset_index(drop=True)


def mirror_symmetry_augment(df: pd.DataFrame, mirror_pairs: dict, enabled: bool = False) -> pd.DataFrame:
    """A-3 (optional, default OFF): relabel one actuator's transitions as a
    nominally-mirrored actuator's, APPENDED with quality halved (weak,
    cross-actuator provenance, never equivalent to a real observation of
    that actuator). mirror_pairs: {actuator_name: mirrored_actuator_name}.
    """
    if not enabled:
        return df
    warnings.warn(
        "mirror_symmetry_augment is ON: this conflicts with the "
        "per-actuator-variability premise this package is built on (each "
        "actuator gets its own fitted model because real actuators are NOT "
        "identical -- gp_code_handoff.md SS7 A-3). Use only as a weak "
        "initializer; default is OFF for a reason.",
        stacklevel=2,
    )
    mirrored = []
    for a_name, mirror_name in mirror_pairs.items():
        sub = df[df["actuator"] == a_name].copy()
        if sub.empty:
            continue
        sub["actuator"] = mirror_name
        sub["quality"] = sub["quality"] * 0.5
        sub["stroke_id"] = sub["stroke_id"].astype(str) + "_mirrored_from_" + a_name
        mirrored.append(sub)
    if not mirrored:
        return df
    return pd.concat([df] + mirrored, ignore_index=True)
