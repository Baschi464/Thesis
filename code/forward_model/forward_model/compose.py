"""
compose.py -- structural (NOT learned) whole-robot rollout F
(gp_code_handoff.md SS6).

F concatenates the 5 independently-fitted per-actuator models; it does
NOT model leg<->bodytail coupling. The mismatch between this composed
rollout and a recorded gait is the transfer-residual measurement (a
separate planned study, per gp_handoff.md's project context) -- this
module only needs to expose the composed rollout (+ per-actuator/total
error, computed in evaluate.py) so that residual can be computed later.

Suction (channels 8/9 in the physical robot; not part of the 5 continuous
actuators modeled here) is SCRIPTED binary state, carried through
untouched -- never predicted by any model.
"""

from typing import Callable, Dict, Optional

import numpy as np


def coupling_correction(z, u):
    """Stub, always zero. Coupling between actuators (e.g. leg loading the
    bodytail arc during stance) is explicitly NOT modeled in this package
    (gp_code_handoff.md SS6) -- the composed rollout's mismatch against a
    recorded real gait IS the transfer-residual measurement, a separate
    planned study. TODO: replace with a learned correction term fit on
    real gait data, stretch goal only, once that data exists.
    """
    return np.zeros_like(np.asarray(z, dtype=float))


class ComposedModel:
    """Wraps one fitted ForwardModel-compatible predictor per actuator
    (any of GPForwardModel, models.PriorPlusGP, LinearForwardModel,
    MLPForwardModel -- anything exposing predict(X)/predict_with_std(X)
    with X columns [z_t, u_t, dir_t])."""

    def __init__(self, actuator_models: Dict[str, object]):
        self.actuator_models = actuator_models

    def predict_step(self, z_now: Dict[str, float], u_now: Dict[str, float],
                      dir_now: Dict[str, float]):
        """One structural step: run each actuator's own model independently
        (no cross-actuator inputs) + the (currently zero) coupling stub."""
        dz = {}
        for name, model in self.actuator_models.items():
            X = np.array([[z_now[name], u_now[name], dir_now[name]]], dtype=float)
            pred = np.asarray(model.predict(X)).ravel()[0]
            corr = float(coupling_correction(np.array([z_now[name]]), np.array([u_now[name]]))[0])
            dz[name] = pred + corr
        return dz

    def rollout(self, z0: Dict[str, float], u_seq: Dict[str, np.ndarray],
                dir_seq: Dict[str, np.ndarray],
                suction_schedule: Optional[Callable[[int], Dict[str, int]]] = None,
                horizon: Optional[int] = None):
        """Roll out all actuators together. u_seq/dir_seq: {actuator:
        array of length >= horizon}. suction_schedule(t) -> {suction_name:
        0/1}, scripted and NOT predicted -- carried through into the output
        under "suction" for downstream joint use, never fed into any dz
        computation.
        """
        names = list(self.actuator_models.keys())
        n = horizon if horizon is not None else min(len(u_seq[name]) for name in names)

        traj = {name: [float(z0[name])] for name in names}
        for t in range(n):
            z_now = {name: traj[name][-1] for name in names}
            u_now = {name: float(u_seq[name][t]) for name in names}
            dir_now = {name: float(dir_seq[name][t]) for name in names}
            dz = self.predict_step(z_now, u_now, dir_now)
            for name in names:
                traj[name].append(z_now[name] + dz[name])

        out = {name: np.array(traj[name]) for name in names}
        if suction_schedule is not None:
            out["suction"] = [suction_schedule(t) for t in range(n)]
        return out


def transfer_residual(rollout_traj: Dict[str, np.ndarray], gait_truth: Dict[str, np.ndarray]):
    """Per-actuator + total RMSE between a composed rollout and a recorded
    (here: synthetic) gait target. This is deliberately exposed but NOT
    interpreted here -- the real transfer-residual study (open-chain vs.
    closed-chain gait) is a separate planned analysis; this just computes
    the number so that study can consume it later.
    """
    per_actuator = {}
    for name, truth in gait_truth.items():
        pred = rollout_traj[name]
        n = min(len(pred), len(truth))
        per_actuator[name] = float(np.sqrt(np.mean((pred[:n] - truth[:n]) ** 2)))
    total = float(np.sqrt(np.mean([v ** 2 for v in per_actuator.values()]))) if per_actuator else float("nan")
    return {"per_actuator_rmse": per_actuator, "total_rmse": total}
