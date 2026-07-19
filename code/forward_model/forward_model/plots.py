"""
plots.py -- diagnostic plots. EVERY plot produced by this module is on
synthetic data (see gp_code_handoff.md honesty constraints) and is titled
/ filed accordingly: titles are prefixed "SYNTHETIC — placeholder",
filenames are prefixed "synthetic_". Do not remove either prefix when
extending this module -- that's the whole point of the constraint.
"""

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

TITLE_PREFIX = "SYNTHETIC — placeholder: "
FILE_PREFIX = "synthetic_"


def _save(fig, out_dir, name):
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"{FILE_PREFIX}{name}.png"
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)
    return path


def plot_data_efficiency(curves: dict, out_dir, actuator: str):
    """curves: {variant_name: {fraction: rmse}}."""
    fig, ax = plt.subplots(figsize=(6, 4.5))
    for variant, curve in curves.items():
        fracs = sorted(curve)
        ax.plot(fracs, [curve[f] for f in fracs], marker="o", label=variant)
    ax.set_xlabel("Fraction of training strokes")
    ax.set_ylabel("One-step RMSE (1/mm)")
    ax.set_title(TITLE_PREFIX + f"data efficiency ({actuator})")
    ax.legend()
    return _save(fig, out_dir, f"data_efficiency_{actuator}")


def plot_rollout_error(horizon_errors: dict, out_dir, actuator: str):
    """horizon_errors: {variant_name: {horizon: rmse}}."""
    fig, ax = plt.subplots(figsize=(6, 4.5))
    for variant, curve in horizon_errors.items():
        hs = sorted(curve)
        ax.plot(hs, [curve[h] for h in hs], marker="o", label=variant)
    ax.set_xlabel("Rollout horizon (frames)")
    ax.set_ylabel("RMSE vs. recorded trajectory (1/mm)")
    ax.set_title(TITLE_PREFIX + f"multi-step rollout error ({actuator})")
    ax.legend()
    return _save(fig, out_dir, f"rollout_error_{actuator}")


def plot_calibration(coverage: dict, out_dir, actuator: str, variant: str):
    """coverage: {sigma_level: {"empirical":..., "nominal":...}} (from
    evaluate.calibration_coverage)."""
    fig, ax = plt.subplots(figsize=(5, 5))
    levels = sorted(coverage)
    nominal = [coverage[k]["nominal"] for k in levels]
    empirical = [coverage[k]["empirical"] for k in levels]
    ax.plot([0, 1], [0, 1], "k--", linewidth=1, label="perfectly calibrated")
    ax.scatter(nominal, empirical, s=60, zorder=5)
    for k, n, e in zip(levels, nominal, empirical):
        ax.annotate(f"±{k}σ", (n, e), textcoords="offset points", xytext=(6, 4))
    ax.set_xlabel("Nominal coverage")
    ax.set_ylabel("Empirical coverage")
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.set_title(TITLE_PREFIX + f"GP calibration ({actuator}, {variant})")
    ax.legend()
    return _save(fig, out_dir, f"calibration_{actuator}_{variant}")


def plot_deadzone_kernel_comparison(u_grid, true_curve, matern_pred, matern_std,
                                     rbf_pred, rbf_std, out_dir, actuator: str,
                                     u_train=None, k_train=None):
    """The RBF-vs-Matern deadzone/"scarp" comparison figure (deliverable #2
    in gp_code_handoff.md SS11) -- shows RBF over-smoothing the reversal
    deadzone vs. Matern following it, on synthetic ground truth.
    """
    fig, ax = plt.subplots(figsize=(7, 5))
    ax.plot(u_grid, true_curve, "k-", linewidth=2, label="true synthetic response")
    ax.plot(u_grid, rbf_pred, color="tab:red", linewidth=2, label="RBF fit")
    ax.fill_between(u_grid, rbf_pred - 2 * rbf_std, rbf_pred + 2 * rbf_std, color="tab:red", alpha=0.15)
    ax.plot(u_grid, matern_pred, color="tab:blue", linewidth=2, label="Matérn-5/2 fit")
    ax.fill_between(u_grid, matern_pred - 2 * matern_std, matern_pred + 2 * matern_std, color="tab:blue", alpha=0.15)
    if u_train is not None and k_train is not None:
        ax.scatter(u_train, k_train, s=12, color="gray", alpha=0.5, label="training points", zorder=1)
    ax.set_xlabel("u_t (commanded steps)")
    ax.set_ylabel("Δκ (1/mm)")
    ax.set_title(TITLE_PREFIX + f"RBF vs Matérn at the reversal deadzone ({actuator})")
    ax.legend(fontsize=8)
    return _save(fig, out_dir, f"rbf_vs_matern_deadzone_{actuator}")


def plot_hysteresis(gaps: list, out_dir, actuator: str, variant: str):
    """gaps: list of {"level","pred_gap","true_gap"} from evaluate.hysteresis_check."""
    if not gaps:
        return None
    fig, ax = plt.subplots(figsize=(6, 4.5))
    levels = [g["level"] for g in gaps]
    ax.plot(levels, [g["true_gap"] for g in gaps], "o-", label="true loading/unloading gap")
    ax.plot(levels, [g["pred_gap"] for g in gaps], "s--", label="model-predicted gap")
    ax.axhline(0, color="gray", linewidth=0.8)
    ax.set_xlabel("Commanded level u_t")
    ax.set_ylabel("Δκ gap (ascend − descend)")
    ax.set_title(TITLE_PREFIX + f"hysteresis reproduction ({actuator}, {variant})")
    ax.legend()
    return _save(fig, out_dir, f"hysteresis_{actuator}_{variant}")
