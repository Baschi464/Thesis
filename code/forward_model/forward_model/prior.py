"""
prior.py -- Variant A: empirical steps->curvature prior g_i(u) + quasi-
static relaxation Delta_prior (gp_code_handoff.md SS5.1).

g_i is fit on HELD STEADY-STATE points from staircase data (the tail of
each held level, where the quasi-static relaxation has mostly settled),
candidates: linear / zero-intercept quadratic / saturating (a*tanh(b*u)),
selected by held-out RMSE. This deliberately naive prior is expected to
miss the reversal deadzone (that's what the GP-on-residual, Variant A's
second stage, is for) and possibly the transient dynamics entirely -- if
its held-out fit is no better than a constant baseline, `prior_weak=True`
is reported so the caller can prefer Variant B (gp_code_handoff.md SS5.1
"Validation hook").

Delta_prior(z_t, u_t, dt) = (g_i(u_t) - z_t) * (1 - exp(-dt/tau))

u_t (not u_tp1) drives this transition -- see synth.py's module docstring;
u_tp1 is only a one-step lookahead used for dir_t/hysteresis-branch
labeling, kept out of the dynamics to stay consistent with models.py's
declared input [z_t, u_t, dir_t].

This quasi-static-relaxation form is ITSELF a modeling choice/approximation
(gp_code_handoff.md SS5.1 explicitly flags this) -- tau is a config
placeholder (prior.tau_s), not a measured time constant.
"""

from dataclasses import dataclass
from typing import Tuple

import numpy as np
import pandas as pd
from scipy.optimize import curve_fit


@dataclass
class PriorModel:
    kind: str            # "linear" | "quad0" | "saturating"
    params: Tuple[float, ...]

    def g(self, u):
        u = np.asarray(u, dtype=float)
        if self.kind == "linear":
            c0, c1 = self.params
            return c0 + c1 * u
        if self.kind == "quad0":
            c1, c2 = self.params
            return c1 * u + c2 * u ** 2
        if self.kind == "saturating":
            a, b = self.params
            return a * np.tanh(b * u)
        raise ValueError(f"unknown prior kind {self.kind}")

    def predict_delta(self, z_t, u_t, dt, tau):
        target = self.g(u_t)
        z_t = np.asarray(z_t, dtype=float)
        dt = np.asarray(dt, dtype=float)
        return (target - z_t) * (1 - np.exp(-dt / tau))


def extract_steady_state_points(df: pd.DataFrame, tail_frac: float = 0.2) -> pd.DataFrame:
    """One (u, kappa) point per stroke: mean of the last `tail_frac` frames
    (by t_host), where the quasi-static relaxation has mostly converged.
    Uses u_t (the command actually driving/held during those tail frames),
    not u_tp1 -- see module docstring."""
    pts = []
    for stroke_id, g in df.groupby("stroke_id"):
        g = g.sort_values("t_host")
        n_tail = max(1, int(np.ceil(len(g) * tail_frac)))
        tail = g.iloc[-n_tail:]
        pts.append({"stroke_id": stroke_id, "u": float(tail["u_t"].iloc[-1]),
                    "kappa": float(tail["kappa_tp1"].mean())})
    return pd.DataFrame(pts)


def _fit_linear(u, k):
    A = np.column_stack([np.ones_like(u), u])
    c0, c1 = np.linalg.lstsq(A, k, rcond=None)[0]
    return (float(c0), float(c1))


def _fit_quad0(u, k):
    A = np.column_stack([u, u ** 2])
    c1, c2 = np.linalg.lstsq(A, k, rcond=None)[0]
    return (float(c1), float(c2))


def _fit_saturating(u, k):
    def f(u, a, b):
        return a * np.tanh(b * u)
    a0 = max(float(np.abs(k).max()), 1e-6)
    b0 = 1.0 / (float(np.abs(u).max()) + 1e-6)
    try:
        popt, _ = curve_fit(f, u, k, p0=[a0, b0], maxfev=5000)
        return (float(popt[0]), float(popt[1]))
    except Exception:
        return (a0, b0)


FIT_FUNCS = {"linear": _fit_linear, "quad0": _fit_quad0, "saturating": _fit_saturating}


def fit_prior(df_staircase: pd.DataFrame, candidates=("linear", "quad0", "saturating"),
              tail_frac: float = 0.2, test_fraction: float = 0.3, seed: int = 0):
    """Fit g_i, select the best candidate by held-out RMSE on the
    steady-state points. Returns (PriorModel, report dict) where report
    has candidate_rmse (all candidates), chosen, held_out_rmse, prior_weak.
    """
    pts = extract_steady_state_points(df_staircase, tail_frac=tail_frac)
    if len(pts) < 4:
        raise ValueError(f"need >=4 steady-state points to fit a prior, got {len(pts)} "
                          "(pass staircase-mode transitions, not jog-only data)")

    rng = np.random.default_rng(seed)
    idx = np.arange(len(pts))
    rng.shuffle(idx)
    n_test = max(1, int(len(idx) * test_fraction))
    test_idx, train_idx = idx[:n_test], idx[n_test:]
    u_all, k_all = pts["u"].to_numpy(), pts["kappa"].to_numpy()
    u_train, k_train = u_all[train_idx], k_all[train_idx]
    u_test, k_test = u_all[test_idx], k_all[test_idx]

    candidate_rmse = {}
    best_kind, best_rmse = None, np.inf
    for kind in candidates:
        params = FIT_FUNCS[kind](u_train, k_train)
        pred = PriorModel(kind, params).g(u_test)
        rmse = float(np.sqrt(np.mean((pred - k_test) ** 2)))
        candidate_rmse[kind] = rmse
        if rmse < best_rmse:
            best_kind, best_rmse = kind, rmse

    # Refit the chosen candidate on ALL steady-state points for deployment.
    final_params = FIT_FUNCS[best_kind](u_all, k_all)
    final_model = PriorModel(best_kind, final_params)

    baseline_rmse = float(np.std(k_test)) if len(k_test) > 1 else np.inf
    prior_weak = bool(best_rmse >= baseline_rmse)

    report = {
        "candidate_rmse": candidate_rmse, "chosen": best_kind,
        "held_out_rmse": best_rmse, "baseline_rmse": baseline_rmse,
        "prior_weak": prior_weak, "n_steady_state_points": len(pts),
    }
    return final_model, report
