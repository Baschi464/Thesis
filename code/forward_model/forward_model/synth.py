"""
synth.py -- synthetic transition generator (gp_code_handoff.md SS4).

THE ONLY DATA SOURCE until real recordings exist (see README.md /
TODO-REAL-DATA.md). Everything downstream (fit/evaluate/compare/rollout)
must be run on this generator's output and labeled SYNTHETIC in every
plot/report filename and title -- never presented as a real result.

Ground truth per actuator (config synth.*):
  kappa_ss(u) = a * tanh(b * u)          -- saturating steps->curvature relation
  with per-actuator (a, b) jitter (manufacturing variability).
  Quasi-static first-order relaxation each frame, DRIVEN BY u_t -- the
  command already in effect for this transition (consistent with
  models.py's declared input [z_t, u_t, dir_t]; u_tp1 is only a one-step
  lookahead used to compute dir_t, it does not drive this transition):
    kappa_{t+1} = kappa_t + (kappa_ss(u_t) - kappa_t) * (1 - exp(-dt/tau))
  A reversal deadzone suppresses most of that delta for the first
  `deadzone.width_steps` of cumulative |Δu| after a direction flip (the
  "scarp" a Matern kernel should capture and RBF should over-smooth).
  Additive Gaussian measurement noise (meas_noise_sd) is applied on top of
  the true noise-free trajectory; the true values are kept in extra columns
  (kappa_t_true/kappa_tp1_true, beyond the canonical schema) so tests/
  evaluation can check recovery against known ground truth.

Two kinds of sequences per actuator, per gp_code_handoff.md SS4:
  - "jog": random step-input commands (matches how real data will be
    collected via jog-like commands).
  - "staircase": ascending/descending held levels (for the prior fit and
    hysteresis test).
Plus an optional synthetic multi-actuator "gait" sequence, written to a
SEPARATE output file -- gait data is target/evaluation only, NEVER forward-
model training data (gp_handoff.md appendix), so it must not silently end
up in the training transitions table.
"""

from pathlib import Path

import numpy as np
import pandas as pd

from . import schema

ACTUATOR_REGIMES = {
    "leg1": ["na"], "leg2": ["na"], "leg3": ["na"], "leg4": ["na"],
    "bodytail": ["ch5", "ch6"],
}


def _kappa_ss(u, a, b):
    return a * np.tanh(b * u)


def _make_levels(rng, mode, cfg):
    if mode == "jog":
        lo, hi = cfg["jog_step_range"]
        levels = []
        for _ in range(cfg["n_strokes_jog"]):
            u = float(rng.uniform(lo, hi))
            n_frames = int(rng.integers(cfg["n_frames_per_stroke"][0], cfg["n_frames_per_stroke"][1] + 1))
            levels.append((u, n_frames))
        return levels
    # staircase: repeat the configured up/down level list n_strokes_staircase times
    levels = []
    for _ in range(cfg["n_strokes_staircase"]):
        for lvl in cfg["staircase_levels"]:
            n_frames = int(rng.integers(cfg["n_frames_per_stroke"][0], cfg["n_frames_per_stroke"][1] + 1))
            levels.append((float(lvl), n_frames))
    return levels


def _flatten_schedule(rng, mode, cfg, actuator_name, regime):
    """One (u_value, stroke_id) per frame -- u_value is the command ALREADY
    active/driving that frame (see module docstring)."""
    schedule = []
    for stroke_idx, (level_u, n_frames) in enumerate(_make_levels(rng, mode, cfg)):
        stroke_id = f"{actuator_name}_{regime}_{mode}_{stroke_idx}"
        schedule.extend([(level_u, stroke_id)] * n_frames)
    return schedule


def _gen_sequence(rng, mode, cfg, a, b, session_id, actuator_name, regime):
    dt = cfg["dt_s"]
    tau = cfg["tau_s"]
    noise_sd = cfg["meas_noise_sd"]
    dz_cfg = cfg["deadzone"]

    schedule = _flatten_schedule(rng, mode, cfg, actuator_name, regime)
    if len(schedule) < 2:
        return []

    rows = []
    kappa = 0.0  # zero-pressure reference start
    kappa0 = 0.0
    last_nonzero_dir = 0
    since_reversal = float("inf")
    t_host = 0.0

    for i in range(len(schedule) - 1):
        u_t, stroke_id = schedule[i]
        u_tp1, _ = schedule[i + 1]

        raw_dir = np.sign(u_tp1 - u_t)
        if raw_dir != 0:
            new_dir = int(raw_dir)
            if last_nonzero_dir != 0 and new_dir != last_nonzero_dir:
                since_reversal = 0.0
            last_nonzero_dir = new_dir
        dir_t = last_nonzero_dir
        since_reversal += abs(u_tp1 - u_t)

        # Driven by u_t (already in effect) -- see module docstring.
        target = _kappa_ss(u_t, a, b)
        raw_delta = (target - kappa) * (1 - np.exp(-dt / tau))
        if dz_cfg["enabled"] and since_reversal < dz_cfg["width_steps"]:
            delta = raw_delta * (1 - dz_cfg["suppression"])
        else:
            delta = raw_delta

        kappa_t_true = kappa
        kappa_tp1_true = kappa + delta
        kappa_t_meas = kappa_t_true + rng.normal(0, noise_sd)
        kappa_tp1_meas = kappa_tp1_true + rng.normal(0, noise_sd)

        rows.append({
            "session_id": session_id, "actuator": actuator_name,
            "t_host": t_host, "dt": dt,
            "kappa_t": kappa_t_meas, "kappa_tp1": kappa_tp1_meas,
            "dkappa": kappa_tp1_meas - kappa_t_meas,
            "u_t": u_t, "u_tp1": u_tp1, "dir_t": dir_t, "regime": regime,
            "kappa0": kappa0, "meas_noise_sd": noise_sd,
            "out_of_plane": False, "quality": 1.0,
            "stroke_id": stroke_id,
            "kappa_t_true": kappa_t_true, "kappa_tp1_true": kappa_tp1_true,
        })

        kappa = kappa_tp1_true  # true state advances noise-free
        t_host += dt

    return rows


def _actuator_params(rng, cfg):
    """Per-actuator (a, b) with manufacturing-variability jitter, one pair
    per (actuator, regime) -- bodytail's ch5/ch6 are physically distinct
    arcs so each gets its own jittered params."""
    a0, b0 = cfg["a_nominal"], cfg["b_nominal"]
    jitter_sd = cfg["n_actuators_jitter_sd"]
    params = {}
    for actuator, regimes in ACTUATOR_REGIMES.items():
        for regime in regimes:
            a = a0 * float(rng.normal(1.0, jitter_sd))
            b = b0 * float(rng.normal(1.0, jitter_sd))
            params[(actuator, regime)] = (a, b)
    return params


def generate_transitions(cfg: dict) -> pd.DataFrame:
    """Main training/eval table: jog + staircase sequences for every
    actuator/regime. NOT the gait sequence (see generate_gait)."""
    synth_cfg = cfg["synth"]
    rng = np.random.default_rng(synth_cfg["seed"])
    params = _actuator_params(rng, synth_cfg)
    session_id = synth_cfg["session_id"]

    all_rows = []
    for (actuator, regime), (a, b) in params.items():
        for mode in ("jog", "staircase"):
            all_rows.extend(_gen_sequence(rng, mode, synth_cfg, a, b, session_id, actuator, regime))

    df = pd.DataFrame(all_rows)
    return schema.validate_transitions(df, require_stroke_id=False)


def generate_gait(cfg: dict) -> pd.DataFrame:
    """Synthetic multi-actuator 'gait' sequence -- coordinated, periodic
    per-actuator commands over n_frames. TARGET/EVALUATION ONLY (see module
    docstring) -- callers must keep this out of any training split. Uses
    the SAME per-actuator ground truth (a, b) as generate_transitions() so a
    composed rollout (compose.py) can be checked against it.
    """
    synth_cfg = cfg["synth"]
    gait_cfg = synth_cfg["gait_sequence"]
    if not gait_cfg.get("enabled", False):
        return pd.DataFrame(columns=list(schema.ALL_COLUMNS) + ["kappa_t_true", "kappa_tp1_true"])

    rng = np.random.default_rng(synth_cfg["seed"] + 1)
    params = _actuator_params(rng, synth_cfg)
    session_id = synth_cfg["session_id"] + "_gait"
    n_frames = gait_cfg["n_frames"]
    dt = synth_cfg["dt_s"]
    lo, hi = synth_cfg["jog_step_range"]
    amp = 0.5 * (hi - lo)

    all_rows = []
    phase_offsets = {"leg1": 0.0, "leg2": np.pi, "leg3": np.pi / 2, "leg4": 1.5 * np.pi,
                      "bodytail": 0.25 * np.pi}
    period_frames = max(10, n_frames // 4)

    for (actuator, regime), (a, b) in params.items():
        phase = phase_offsets.get(actuator, 0.0)
        # Precompute the full command schedule so u_t (driving this frame)
        # and u_tp1 (lookahead, for dir_t) follow the same convention as
        # _gen_sequence -- see module docstring.
        u_schedule = [float(amp * np.sin(2 * np.pi * f / period_frames + phase)) for f in range(n_frames + 1)]
        kappa = 0.0
        last_nonzero_dir = 0
        since_reversal = float("inf")
        t_host = 0.0
        stroke_id = f"{actuator}_{regime}_gait"
        for frame in range(n_frames):
            u_t = u_schedule[frame]
            u_tp1 = u_schedule[frame + 1]
            raw_dir = np.sign(u_tp1 - u_t)
            if raw_dir != 0:
                new_dir = int(raw_dir)
                if last_nonzero_dir != 0 and new_dir != last_nonzero_dir:
                    since_reversal = 0.0
                last_nonzero_dir = new_dir
            dir_t = last_nonzero_dir
            since_reversal += abs(u_tp1 - u_t)

            dz_cfg = synth_cfg["deadzone"]
            target = _kappa_ss(u_t, a, b)
            raw_delta = (target - kappa) * (1 - np.exp(-dt / synth_cfg["tau_s"]))
            delta = raw_delta * (1 - dz_cfg["suppression"]) if (dz_cfg["enabled"] and since_reversal < dz_cfg["width_steps"]) else raw_delta

            kappa_t_true = kappa
            kappa_tp1_true = kappa + delta
            noise_sd = synth_cfg["meas_noise_sd"]
            kappa_t_meas = kappa_t_true + rng.normal(0, noise_sd)
            kappa_tp1_meas = kappa_tp1_true + rng.normal(0, noise_sd)

            all_rows.append({
                "session_id": session_id, "actuator": actuator,
                "t_host": t_host, "dt": dt,
                "kappa_t": kappa_t_meas, "kappa_tp1": kappa_tp1_meas,
                "dkappa": kappa_tp1_meas - kappa_t_meas,
                "u_t": u_t, "u_tp1": u_tp1, "dir_t": dir_t, "regime": regime,
                "kappa0": 0.0, "meas_noise_sd": noise_sd,
                "out_of_plane": False, "quality": 1.0, "stroke_id": stroke_id,
                "kappa_t_true": kappa_t_true, "kappa_tp1_true": kappa_tp1_true,
            })
            kappa = kappa_tp1_true
            t_host += dt

    df = pd.DataFrame(all_rows)
    return schema.validate_transitions(df, require_stroke_id=False)


def write_synthetic_dataset(cfg: dict, out_path: str, gait_out_path: str = None):
    df = generate_transitions(cfg)
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(out_path, index=False)
    print(f"SYNTHETIC transitions written -> {out_path} ({len(df)} rows)")

    if gait_out_path is not None and cfg["synth"]["gait_sequence"].get("enabled", False):
        gait_df = generate_gait(cfg)
        gait_out_path = Path(gait_out_path)
        gait_out_path.parent.mkdir(parents=True, exist_ok=True)
        gait_df.to_parquet(gait_out_path, index=False)
        print(f"SYNTHETIC gait sequence written -> {gait_out_path} ({len(gait_df)} rows) "
              f"-- target/evaluation only, never training data")

    return df
