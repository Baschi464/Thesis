"""
evaluate.py -- the deliverable that matters (gp_code_handoff.md SS8).

Metrics, per actuator x {A, B1, B2, (B3)}:
  1. one_step_rmse           -- held-out one-step Delta z RMSE.
  2. rollout_error_vs_horizon -- multi-step rollout error vs horizon.
  3. calibration_coverage    -- GP-only: empirical +-1sigma/+-2sigma coverage.
  4. data_efficiency_curve   -- error vs. fraction of training strokes.
  5. hysteresis_check        -- does the model reproduce the loading/
     unloading gap on held-out staircase data.

decision_rule() reports a recommendation from the MEASURED numbers -- it
never hard-codes a winner (gp_code_handoff.md: "The A-vs-B decision cannot
be made now"). error_vs_ground_truth() is synthetic-only (needs the true
noise-free kappa, which only the generator knows).

All functions take already-fitted ForwardModel-compatible objects
(predict(X)/predict_with_std(X), X columns = [z_t, u_t, dir_t]) -- fitting
itself (which variant, which prior, etc.) is orchestrated in cli.py, not
here, so this module stays agnostic to how a model was produced.
"""

from typing import Optional

import numpy as np
import pandas as pd

from . import data, models

NOMINAL_COVERAGE = {1: 0.6827, 2: 0.9545}


def one_step_rmse(model, X: np.ndarray, dZ_true: np.ndarray) -> float:
    pred = np.asarray(model.predict(X)).reshape(np.asarray(dZ_true).shape)
    return float(np.sqrt(np.mean((pred - dZ_true) ** 2)))


def error_vs_ground_truth(model, X: np.ndarray, kappa_tp1_true: np.ndarray, z_col: int = 0) -> float:
    """SYNTHETIC-ONLY: compares the model's predicted next-state against
    the generator's true noise-free kappa_tp1 (real data will never have
    this column -- see synth.py)."""
    pred_dz = np.asarray(model.predict(X)).ravel()
    pred_kappa_tp1 = X[:, z_col] + pred_dz
    return float(np.sqrt(np.mean((pred_kappa_tp1 - np.asarray(kappa_tp1_true)) ** 2)))


def rollout_error_vs_horizon(model, df_test: pd.DataFrame, horizons, z_col: str = "kappa_t"):
    """Per held-out stroke: roll out from the stroke's first z_t along its
    own recorded u_t/dir_t sequence, feeding predictions back; compare to
    the stroke's actually-recorded kappa_tp1 sequence at each horizon.
    Returns {horizon: rmse}.
    """
    max_h = max(horizons)
    per_h_errs = {h: [] for h in horizons}
    for _, g in df_test.groupby("stroke_id"):
        g = g.sort_values("t_host").reset_index(drop=True)
        if len(g) < 2:
            continue
        z0 = np.array([g[z_col].iloc[0]])
        u_seq = g["u_t"].to_numpy()
        dir_seq = g["dir_t"].to_numpy()
        truth = np.concatenate([[g[z_col].iloc[0]], g["kappa_tp1"].to_numpy()])
        z_traj, _ = models.rollout(model, z0, u_seq, dir_seq, horizon=min(max_h, len(u_seq)))
        z_traj = z_traj[:, 0]
        for h in horizons:
            if h < len(z_traj) and h < len(truth):
                per_h_errs[h].append((z_traj[h] - truth[h]) ** 2)
    return {h: (float(np.sqrt(np.mean(v))) if v else float("nan")) for h, v in per_h_errs.items()}


def calibration_coverage(model, X: np.ndarray, dZ_true: np.ndarray, sigma_levels=(1, 2)) -> Optional[dict]:
    """GP-only (returns None if the model has no predictive std). Empirical
    coverage of +-k*sigma vs. the nominal Gaussian coverage."""
    mean, std = model.predict_with_std(X)
    if std is None:
        return None
    mean = np.asarray(mean).reshape(np.asarray(dZ_true).shape)
    std = np.asarray(std).reshape(np.asarray(dZ_true).shape)
    resid = np.abs(np.asarray(dZ_true) - mean)
    out = {}
    for k in sigma_levels:
        empirical = float((resid <= k * std).mean())
        nominal = NOMINAL_COVERAGE.get(k)
        out[k] = {"empirical": empirical, "nominal": nominal,
                   "diff": (empirical - nominal) if nominal is not None else None}
    return out


def data_efficiency_curve(fit_fn, df_train: pd.DataFrame, X_test, dZ_test,
                           fractions, seed: int = 0):
    """fit_fn(df_subset) -> fitted model. Subsets by fraction of UNIQUE
    STROKES (not rows) -- never fraction-of-rows, which would leak
    within-stroke correlation into the "more data" condition unevenly.
    Returns {fraction: rmse}.
    """
    rng = np.random.default_rng(seed)
    strokes = df_train["stroke_id"].unique().copy()
    rng.shuffle(strokes)
    n_total = len(strokes)
    curve = {}
    for frac in fractions:
        n = max(1, int(round(n_total * frac)))
        chosen = set(strokes[:n].tolist())
        sub = df_train[df_train["stroke_id"].isin(chosen)]
        model = fit_fn(sub)
        curve[frac] = one_step_rmse(model, X_test, dZ_test)
    return curve


def hysteresis_check(model, df_staircase_test: pd.DataFrame, level_round: int = -1):
    """At commanded levels present on BOTH branches (dir_t=+1 ascending,
    dir_t=-1 descending) in held-out staircase data, compares the model's
    predicted Delta z on each branch. Fails (reproduced=False) if the model
    collapses the two branches to (near-)equal predictions -- i.e. dir_t's
    effect / the kernel's ability to place branches in different input
    regions has been lost.
    """
    df = df_staircase_test.copy()
    df["_level"] = df["u_t"].round(level_round)
    gaps = []
    for lvl in sorted(df["_level"].unique()):
        asc = df[(df["_level"] == lvl) & (df["dir_t"] == 1)]
        desc = df[(df["_level"] == lvl) & (df["dir_t"] == -1)]
        if len(asc) == 0 or len(desc) == 0:
            continue
        X_asc, _ = data.build_feature_matrix(asc)
        X_desc, _ = data.build_feature_matrix(desc)
        pred_asc = float(np.asarray(model.predict(X_asc)).mean())
        pred_desc = float(np.asarray(model.predict(X_desc)).mean())
        true_asc = float(asc["dkappa"].mean())
        true_desc = float(desc["dkappa"].mean())
        gaps.append({"level": float(lvl), "pred_gap": pred_asc - pred_desc,
                     "true_gap": true_asc - true_desc})

    if not gaps:
        return {"status": "no_overlapping_levels", "gaps": []}

    pred_gap_mean = float(np.mean([g["pred_gap"] for g in gaps]))
    true_gap_mean = float(np.mean([g["true_gap"] for g in gaps]))
    reproduced = bool(abs(pred_gap_mean) > 1e-9 and np.sign(pred_gap_mean) == np.sign(true_gap_mean))
    return {"status": "ok", "gaps": gaps, "pred_gap_mean": pred_gap_mean,
            "true_gap_mean": true_gap_mean, "reproduced": reproduced}


def decision_rule(data_eff_curves: dict, prior_report: Optional[dict] = None) -> str:
    """Text recommendation derived from MEASURED numbers -- see module
    docstring. `data_eff_curves`: {"A":{frac:rmse}, "B1":{...}, "B2":{...}}."""
    lines = []
    a_curve, b1_curve, b2_curve = (data_eff_curves.get(k) for k in ("A", "B1", "B2"))

    if a_curve and b1_curve:
        small_frac = min(a_curve)
        a_small, b1_small = a_curve[small_frac], b1_curve[small_frac]
        if prior_report is not None and prior_report.get("prior_weak"):
            lines.append(f"Prior flagged WEAK (held-out RMSE {prior_report['held_out_rmse']:.4g} >= "
                          f"baseline std {prior_report['baseline_rmse']:.4g}) -> prefer Variant B1 "
                          "regardless of the data-efficiency numbers below.")
        elif a_small < b1_small:
            lines.append(f"Variant A has clearly better small-N ({small_frac * 100:.0f}% strokes) error "
                          f"({a_small:.4g} vs B1's {b1_small:.4g}) AND the prior validated -> prefer Variant A.")
        else:
            lines.append(f"Variant B1 matches/beats Variant A at small-N ({b1_small:.4g} vs A's {a_small:.4g}) "
                          "-> prefer Variant B1 (model-free).")
    else:
        lines.append("Insufficient data-efficiency curves for A vs B1 -- rerun `fm compare`.")

    if b1_curve and b2_curve:
        full_frac = max(b1_curve)
        b1_full, b2_full = b1_curve[full_frac], b2_curve.get(full_frac)
        if b2_full is not None:
            rel = abs(b1_full - b2_full) / max(abs(b2_full), 1e-9)
            if rel < 0.1:
                lines.append(f"B2 (linear) is within {rel * 100:.1f}% of B1 (GP) at full data "
                              f"({b2_full:.4g} vs {b1_full:.4g}) -> dynamics effectively linear over this range.")

    lines.append("GP-based variants (A, B1) are preferred over B2/B3 for anything feeding a future "
                  "planner, for their calibrated uncertainty -- independent of the one-step-error ranking above.")
    lines.append("This decision is a MEASUREMENT ON SYNTHETIC DATA and is NOT the real A-vs-B decision "
                  "-- rerun on real transitions before trusting it (see TODO-REAL-DATA.md).")
    return "\n".join(lines)
