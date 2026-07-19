"""
cli.py -- fm gen-synth | fit | evaluate | compare | rollout
(gp_code_handoff.md SS9). Orchestration only: which variant gets fit how,
which metrics get run, report/plot assembly -- the actual modeling logic
lives in prior.py/models.py/evaluate.py.

EVERYTHING this CLI produces right now is on synthetic data (synth.py is
the only data source until real recordings exist) -- every output path
under outputs/ is prefixed accordingly, every report says so explicitly.
"""

import argparse
import pickle
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

from . import augment, compose, data, evaluate, models, plots, prior, synth

HERE = Path(__file__).resolve().parent
DEFAULT_CONFIG = HERE.parent / "config" / "default.yaml"

ACTUATOR_NAMES = ["leg1", "leg2", "leg3", "leg4", "bodytail"]


def load_config(path):
    with open(path) as f:
        return yaml.safe_load(f)


def _is_staircase(df: pd.DataFrame) -> pd.Series:
    """Synthetic-only heuristic: synth.py tags stroke_id with the
    generating mode ("jog"/"staircase"). Real recordings won't have this
    substring convention -- select staircase-session data by session_id/
    metadata instead once real data exists (see TODO-REAL-DATA.md)."""
    return df["stroke_id"].astype(str).str.contains("staircase")


def fit_variant(variant: str, df: pd.DataFrame, cfg: dict, seed: int = 0):
    """Fit one variant on df (already filtered to one actuator/regime).
    Returns (model, extra) where model exposes predict(X)/predict_with_std(X)
    uniformly and extra carries variant-specific diagnostics (e.g. Variant
    A's prior report)."""
    z_cols = ("kappa_t",)
    X, dZ = data.build_feature_matrix(df, z_cols=z_cols)
    dt_repr = float(df["dt"].median())

    if variant == "B2":
        m = models.LinearForwardModel(**cfg["linear"])
        m.fit(X, dZ)
        return m, {}

    if variant == "B3":
        mlp_cfg = {k: v for k, v in cfg["mlp"].items() if k != "enabled"}
        m = models.MLPForwardModel(**mlp_cfg)
        m.fit(X, dZ)
        return m, {}

    if variant == "B1":
        m = models.GPForwardModel(mode="delta", random_state=seed, **cfg["gp"])
        m.fit(X, dZ)
        return m, {}

    if variant == "A":
        staircase_df = df[_is_staircase(df)]
        if len(staircase_df) == 0:
            raise ValueError("Variant A needs staircase-mode transitions to fit the prior "
                              "(none found -- check stroke_id / session selection)")
        prior_model, prior_report = prior.fit_prior(
            staircase_df, candidates=cfg["prior"]["candidates"], seed=seed)
        tau = cfg["prior"]["tau_s"]
        dZ_prior = prior_model.predict_delta(
            df["kappa_t"].to_numpy(), df["u_t"].to_numpy(), df["dt"].to_numpy(), tau
        ).reshape(-1, 1)
        gp = models.GPForwardModel(mode="residual", random_state=seed, **cfg["gp"])
        gp.fit(X, dZ, dZ_prior=dZ_prior)
        wrapped = models.PriorPlusGP(prior_model, gp, tau, dt_repr)
        return wrapped, {"prior_report": prior_report}

    raise ValueError(f"unknown variant {variant!r}")


def _prep_actuator_df(args, cfg):
    df_all = data.load_transitions(
        args.data, group_held_frames=cfg["augment"]["held_frame_grouping"])
    df = data.filter_actuator(df_all, args.actuator, regime=getattr(args, "regime", None))
    if cfg["augment"]["measured_noise_jitter"]:
        z_cols = ("kappa_t",)
        X, dZ = data.build_feature_matrix(df, z_cols=z_cols)
        rng = np.random.default_rng(cfg["split"]["seed"])
        X = augment.jitter_z(X, df["meas_noise_sd"].to_numpy(), jitter_scale=cfg["augment"]["jitter_scale"],
                              n_state_dims=len(z_cols), rng=rng)
        df = df.copy()
        df["kappa_t"] = X[:, 0]
    return df


def cmd_gen_synth(args):
    cfg = load_config(args.config)
    synth.write_synthetic_dataset(cfg, args.out, gait_out_path=args.gait_out)


def cmd_fit(args):
    cfg = load_config(args.config)
    df = _prep_actuator_df(args, cfg)
    model, extra = fit_variant(args.variant, df, cfg, seed=cfg["split"]["seed"])

    out_path = Path(args.out) if args.out else (
        HERE.parent / cfg["paths"]["outputs_dir"] / "models" / f"{args.actuator}_{args.variant}.pkl")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "wb") as f:
        pickle.dump({"model": model, "variant": args.variant, "actuator": args.actuator,
                     "regime": args.regime, "extra": extra}, f)
    print(f"SYNTHETIC-data fit: {args.variant} for {args.actuator} -> {out_path}")
    if "prior_report" in extra:
        print("Prior report:", extra["prior_report"])


def cmd_evaluate(args):
    cfg = load_config(args.config)
    df = _prep_actuator_df(args, cfg)
    df_train, df_test = data.stroke_wise_split(
        df, cfg["split"]["test_fraction"], cfg["split"]["hold_out_levels"], cfg["split"]["seed"])

    model, extra = fit_variant(args.variant, df_train, cfg, seed=cfg["split"]["seed"])
    z_cols = ("kappa_t",)
    X_test, dZ_test = data.build_feature_matrix(df_test, z_cols=z_cols)

    out_dir = Path(args.out_dir or (HERE.parent / cfg["paths"]["outputs_dir"] / "evaluate" / args.actuator / args.variant))
    out_dir.mkdir(parents=True, exist_ok=True)

    report_lines = [f"# SYNTHETIC evaluation -- {args.actuator} / {args.variant}", ""]

    rmse = evaluate.one_step_rmse(model, X_test, dZ_test)
    report_lines.append(f"1. One-step RMSE (held-out): {rmse:.5g}")

    if "kappa_tp1_true" in df_test.columns:
        gt_rmse = evaluate.error_vs_ground_truth(model, X_test, df_test["kappa_tp1_true"].to_numpy())
        report_lines.append(f"   Error vs. synthetic ground truth: {gt_rmse:.5g}")

    horizons = cfg["evaluate"]["rollout_horizons"]
    rollout_err = evaluate.rollout_error_vs_horizon(model, df_test, horizons)
    report_lines.append(f"2. Rollout error vs horizon: {rollout_err}")
    plots.plot_rollout_error({args.variant: rollout_err}, out_dir, args.actuator)

    coverage = evaluate.calibration_coverage(model, X_test, dZ_test, cfg["evaluate"]["calibration_sigma_levels"])
    if coverage is not None:
        report_lines.append(f"3. Calibration coverage: {coverage}")
        plots.plot_calibration(coverage, out_dir, args.actuator, args.variant)
    else:
        report_lines.append("3. Calibration: N/A (non-probabilistic model)")

    def _fit_fn(sub_df):
        m, _ = fit_variant(args.variant, sub_df, cfg, seed=cfg["split"]["seed"])
        return m
    eff_curve = evaluate.data_efficiency_curve(
        _fit_fn, df_train, X_test, dZ_test, cfg["evaluate"]["data_efficiency_fractions"], seed=cfg["split"]["seed"])
    report_lines.append(f"4. Data-efficiency curve: {eff_curve}")
    plots.plot_data_efficiency({args.variant: eff_curve}, out_dir, args.actuator)

    staircase_test = df_test[_is_staircase(df_test)]
    hyst = evaluate.hysteresis_check(model, staircase_test) if len(staircase_test) else {"status": "no_staircase_data"}
    report_lines.append(f"5. Hysteresis check: {hyst}")
    if hyst.get("gaps"):
        plots.plot_hysteresis(hyst["gaps"], out_dir, args.actuator, args.variant)

    report_path = out_dir / "synthetic_evaluate_report.md"
    report_path.write_text("\n".join(str(l) for l in report_lines))
    print("\n".join(str(l) for l in report_lines))
    print(f"\nWrote report + plots -> {out_dir}")


def cmd_compare(args):
    cfg = load_config(args.config)
    df = _prep_actuator_df(args, cfg)
    df_train, df_test = data.stroke_wise_split(
        df, cfg["split"]["test_fraction"], cfg["split"]["hold_out_levels"], cfg["split"]["seed"])

    variants = ["A", "B1", "B2"]
    if cfg["mlp"]["enabled"]:
        variants.append("B3")

    z_cols = ("kappa_t",)
    X_test, dZ_test = data.build_feature_matrix(df_test, z_cols=z_cols)
    out_dir = Path(args.out_dir or (HERE.parent / cfg["paths"]["outputs_dir"] / "compare" / args.actuator))
    out_dir.mkdir(parents=True, exist_ok=True)

    one_step, rollout_curves, eff_curves, hyst_results, cal_results = {}, {}, {}, {}, {}
    extras = {}
    horizons = cfg["evaluate"]["rollout_horizons"]
    staircase_test = df_test[_is_staircase(df_test)]

    for variant in variants:
        model, extra = fit_variant(variant, df_train, cfg, seed=cfg["split"]["seed"])
        extras[variant] = extra
        one_step[variant] = evaluate.one_step_rmse(model, X_test, dZ_test)
        rollout_curves[variant] = evaluate.rollout_error_vs_horizon(model, df_test, horizons)

        cov = evaluate.calibration_coverage(model, X_test, dZ_test, cfg["evaluate"]["calibration_sigma_levels"])
        if cov is not None:
            cal_results[variant] = cov
            plots.plot_calibration(cov, out_dir, args.actuator, variant)

        def _fit_fn(sub_df, variant=variant):
            m, _ = fit_variant(variant, sub_df, cfg, seed=cfg["split"]["seed"])
            return m
        eff_curves[variant] = evaluate.data_efficiency_curve(
            _fit_fn, df_train, X_test, dZ_test, cfg["evaluate"]["data_efficiency_fractions"], seed=cfg["split"]["seed"])

        if len(staircase_test):
            hyst_results[variant] = evaluate.hysteresis_check(model, staircase_test)
            if hyst_results[variant].get("gaps"):
                plots.plot_hysteresis(hyst_results[variant]["gaps"], out_dir, args.actuator, variant)

    plots.plot_data_efficiency(eff_curves, out_dir, args.actuator)
    plots.plot_rollout_error(rollout_curves, out_dir, args.actuator)

    # RBF-vs-Matern deadzone comparison figure (deliverable #2): refit B1
    # with each kernel on this actuator's data and compare near the deadzone.
    kernel_curves = {}
    u_grid = np.linspace(df_train["u_t"].min(), df_train["u_t"].max(), 200)
    z_at_grid = np.full_like(u_grid, df_train["kappa_t"].median())
    dir_at_grid = np.ones_like(u_grid)
    X_grid = np.column_stack([z_at_grid, u_grid, dir_at_grid])
    for kernel_name in ("rbf_ard", "matern52_ard"):
        gp_cfg = dict(cfg["gp"])
        gp_cfg["kernel"] = kernel_name
        m = models.GPForwardModel(mode="delta", random_state=cfg["split"]["seed"], **gp_cfg)
        X_train, dZ_train = data.build_feature_matrix(df_train, z_cols=z_cols)
        m.fit(X_train, dZ_train)
        mean, std = m.predict_with_std(X_grid)
        kernel_curves[kernel_name] = (mean.ravel(), std.ravel())
    true_curve = np.full_like(u_grid, np.nan)  # no closed-form ground truth for Delta z at arbitrary z; left NaN, kept for API symmetry
    plots.plot_deadzone_kernel_comparison(
        u_grid, true_curve, kernel_curves["matern52_ard"][0], kernel_curves["matern52_ard"][1],
        kernel_curves["rbf_ard"][0], kernel_curves["rbf_ard"][1], out_dir, args.actuator,
        u_train=df_train["u_t"].to_numpy(), k_train=df_train["dkappa"].to_numpy())

    prior_report = extras.get("A", {}).get("prior_report")
    decision = evaluate.decision_rule(eff_curves, prior_report)

    report = [f"# SYNTHETIC comparison report -- {args.actuator}", "",
              "All numbers below are measured on the synthetic generator's output "
              "(synth.py) -- NOT real robot data. See README.md / TODO-REAL-DATA.md.", "",
              "## One-step RMSE (held-out)"]
    for v in variants:
        report.append(f"- {v}: {one_step[v]:.5g}")
    report += ["", "## Multi-step rollout RMSE vs horizon"]
    for v in variants:
        report.append(f"- {v}: {rollout_curves[v]}")
    report += ["", "## Data-efficiency curves (RMSE vs fraction of training strokes)"]
    for v in variants:
        report.append(f"- {v}: {eff_curves[v]}")
    report += ["", "## Calibration (GP variants only)"]
    for v, cov in cal_results.items():
        report.append(f"- {v}: {cov}")
    report += ["", "## Hysteresis reproduction"]
    for v, h in hyst_results.items():
        report.append(f"- {v}: {h}")
    if "A" in extras and "prior_report" in extras["A"]:
        report += ["", "## Variant A prior report", f"{extras['A']['prior_report']}"]
    report += ["", "## Decision (report, not hard-coded)", decision]

    report_path = out_dir / "synthetic_compare_report.md"
    report_path.write_text("\n".join(report))
    print("\n".join(report))
    print(f"\nWrote report + plots -> {out_dir}")


def cmd_rollout(args):
    cfg = load_config(args.config)
    df_all = data.load_transitions(args.data, group_held_frames=cfg["augment"]["held_frame_grouping"])
    gait_df = pd.read_parquet(args.gait)

    print("NOTE: this checks the COMPOSITION MACHINERY on synthetic, "
          "deliberately-uncoupled data -- it validates that rollout/compose "
          "code runs end-to-end, it does NOT demonstrate or measure the real "
          "leg<->bodytail coupling effect (that requires real recorded gait "
          "data -- see compose.py module docstring / TODO-REAL-DATA.md).")

    actuator_models = {}
    z0, u_seq, dir_seq = {}, {}, {}
    for actuator in ACTUATOR_NAMES:
        regimes = ["ch5", "ch6"] if actuator == "bodytail" else [None]
        for regime in regimes:
            key = actuator if regime is None else f"{actuator}_{regime}"
            df_a = data.filter_actuator(df_all, actuator, regime=regime)
            if len(df_a) == 0:
                continue
            model, _ = fit_variant(args.variant, df_a, cfg, seed=cfg["split"]["seed"])
            actuator_models[key] = model

            g_a = gait_df[gait_df["actuator"] == actuator]
            if regime is not None:
                g_a = g_a[g_a["regime"] == regime]
            g_a = g_a.sort_values("t_host")
            if len(g_a) == 0:
                continue
            z0[key] = float(g_a["kappa_t"].iloc[0])
            u_seq[key] = g_a["u_t"].to_numpy()
            dir_seq[key] = g_a["dir_t"].to_numpy()

    composed = compose.ComposedModel(actuator_models)
    traj = composed.rollout(z0, u_seq, dir_seq)

    gait_truth = {}
    for key in actuator_models:
        parts = key.split("_")
        actuator = parts[0] if parts[0] != "bodytail" else "bodytail"
        regime = parts[1] if len(parts) > 1 and actuator == "bodytail" else None
        g_a = gait_df[gait_df["actuator"] == actuator]
        if regime is not None:
            g_a = g_a[g_a["regime"] == regime]
        g_a = g_a.sort_values("t_host")
        truth = np.concatenate([[g_a["kappa_t"].iloc[0]], g_a["kappa_tp1"].to_numpy()])
        gait_truth[key] = truth

    residual = compose.transfer_residual(traj, gait_truth)

    out_dir = Path(args.out_dir or (HERE.parent / cfg["paths"]["outputs_dir"] / "rollout"))
    out_dir.mkdir(parents=True, exist_ok=True)
    report_path = out_dir / "synthetic_rollout_report.md"
    report_path.write_text(
        "# SYNTHETIC composed rollout vs synthetic gait target\n\n"
        "This is a synthetic self-consistency check of the composition "
        "machinery, NOT a real transfer-residual measurement.\n\n"
        f"Per-actuator RMSE: {residual['per_actuator_rmse']}\n\n"
        f"Total RMSE: {residual['total_rmse']:.5g}\n"
    )
    print(f"Per-actuator RMSE: {residual['per_actuator_rmse']}")
    print(f"Total RMSE: {residual['total_rmse']:.5g}")
    print(f"Wrote report -> {report_path}")


def main(argv=None):
    parser = argparse.ArgumentParser(prog="fm", description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    p_gen = sub.add_parser("gen-synth", help="generate the synthetic transitions table")
    p_gen.add_argument("--config", default=str(DEFAULT_CONFIG))
    p_gen.add_argument("--out", default=str(HERE.parent / "outputs" / "transitions_synth.parquet"))
    p_gen.add_argument("--gait-out", default=str(HERE.parent / "outputs" / "transitions_synth_gait.parquet"))

    def _common_fit_args(p):
        p.add_argument("--config", default=str(DEFAULT_CONFIG))
        p.add_argument("--data", required=True)
        p.add_argument("--actuator", required=True, choices=ACTUATOR_NAMES)
        p.add_argument("--regime", default=None, choices=[None, "ch5", "ch6"])

    p_fit = sub.add_parser("fit", help="fit one variant for one actuator")
    _common_fit_args(p_fit)
    p_fit.add_argument("--variant", required=True, choices=["A", "B1", "B2", "B3"])
    p_fit.add_argument("--out", default=None)

    p_eval = sub.add_parser("evaluate", help="metrics 1-5 + plots for one variant")
    _common_fit_args(p_eval)
    p_eval.add_argument("--variant", required=True, choices=["A", "B1", "B2", "B3"])
    p_eval.add_argument("--out-dir", default=None)

    p_cmp = sub.add_parser("compare", help="run A/B1/B2(/B3), data-efficiency curves, report")
    _common_fit_args(p_cmp)
    p_cmp.add_argument("--out-dir", default=None)

    p_roll = sub.add_parser("rollout", help="composed F rollout vs synthetic gait target")
    p_roll.add_argument("--config", default=str(DEFAULT_CONFIG))
    p_roll.add_argument("--data", required=True)
    p_roll.add_argument("--gait", required=True)
    p_roll.add_argument("--variant", default="B1", choices=["A", "B1", "B2", "B3"])
    p_roll.add_argument("--out-dir", default=None)

    args = parser.parse_args(argv)
    {
        "gen-synth": cmd_gen_synth, "fit": cmd_fit, "evaluate": cmd_evaluate,
        "compare": cmd_compare, "rollout": cmd_rollout,
    }[args.command](args)


if __name__ == "__main__":
    sys.exit(main())
