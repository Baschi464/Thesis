"""
data.py -- load/validate transitions, stroke-wise split, standardization.

Held-frame grouping (gp_code_handoff.md's "A-2" augmentation) is
implemented in augment.py (it's explicitly an augmentation technique per
SS7); this module exposes a thin pass-through so the load pipeline can
apply it in one place -- see load_transitions(group_held_frames=...).
"""

from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd

from . import schema


def _infer_stroke_id(df: pd.DataFrame) -> pd.DataFrame:
    """Best-effort stroke_id when upstream data doesn't provide one:
    a stroke = a maximal contiguous run (by t_host order) of constant
    (session_id, actuator, regime, dir_t, u_tp1). Real data should emit
    stroke_id directly once the recording pipeline defines it explicitly
    (see TODO-REAL-DATA.md) -- this is a fallback, not the primary path.
    """
    df = df.sort_values(["session_id", "actuator", "regime", "t_host"]).reset_index(drop=True)
    key = list(zip(df["session_id"], df["actuator"], df["regime"], df["dir_t"], df["u_tp1"]))
    stroke_num = [0]
    for i in range(1, len(key)):
        stroke_num.append(stroke_num[-1] + (1 if key[i] != key[i - 1] else 0))
    df["stroke_id"] = [f"inferred_{n}" for n in stroke_num]
    return df


def load_transitions(path, allow_cross_session: bool = False,
                      home_alignment: Optional[dict] = None,
                      group_held_frames: bool = False,
                      held_frame_tol: float = 1e-6) -> pd.DataFrame:
    """Load + validate a transitions parquet/csv. Applies the cross-session
    guard (schema.check_single_session) and infers stroke_id if absent.
    """
    path = Path(path)
    if path.suffix == ".csv":
        df = pd.read_csv(path)
    else:
        df = pd.read_parquet(path)

    df = schema.validate_transitions(df, require_stroke_id=False)
    schema.check_single_session(df, allow_cross_session, home_alignment)

    if df["stroke_id"].isna().all():
        df = _infer_stroke_id(df)

    if group_held_frames:
        from . import augment
        df = augment.group_held_frames(df, tol=held_frame_tol)

    return df


def filter_actuator(df: pd.DataFrame, actuator: str, regime: Optional[str] = None,
                     exclude_out_of_plane: bool = True, min_quality: float = 0.0) -> pd.DataFrame:
    """Subset to one actuator (+ optional regime, for bodytail's ch5/ch6),
    dropping flagged-bad frames. Never silently includes out-of-plane
    frames -- see plan v2 SS8.2 / handoff guardrails this project already
    follows upstream in the vision pipeline."""
    out = df[df["actuator"] == actuator]
    if regime is not None:
        out = out[out["regime"] == regime]
    if exclude_out_of_plane:
        out = out[~out["out_of_plane"]]
    if min_quality > 0:
        out = out[out["quality"] >= min_quality]
    return out.reset_index(drop=True)


def stroke_wise_split(df: pd.DataFrame, test_fraction: float, hold_out_levels: bool,
                       seed: int = 0):
    """Split by whole strokes (never individual rows -- consecutive frames
    are correlated, a random row split would leak). If hold_out_levels,
    prefer holding out whole commanded-step "levels" (u_tp1 rounded to the
    nearest 10 steps) so test also covers interpolation/mild extrapolation,
    not just unseen noise realizations of already-seen levels.
    """
    if df.empty:
        return df.copy(), df.copy()

    rng = np.random.default_rng(seed)
    strokes = df.groupby("stroke_id").agg(
        n=("stroke_id", "size"),
        level=("u_tp1", lambda x: round(float(x.iloc[-1]), -1)),
    )
    total = int(strokes["n"].sum())
    target_test = total * test_fraction

    test_ids = []
    if hold_out_levels:
        levels = strokes["level"].unique()
        rng.shuffle(levels)
        acc = 0
        for lvl in levels:
            if acc >= target_test:
                break
            ids = strokes.index[strokes["level"] == lvl].tolist()
            test_ids.extend(ids)
            acc += int(strokes.loc[ids, "n"].sum())
    else:
        ids = strokes.index.to_numpy().copy()
        rng.shuffle(ids)
        acc = 0
        for sid in ids:
            if acc >= target_test:
                break
            test_ids.append(sid)
            acc += int(strokes.loc[sid, "n"])

    test_mask = df["stroke_id"].isin(test_ids)
    train_df = df[~test_mask].reset_index(drop=True)
    test_df = df[test_mask].reset_index(drop=True)
    overlap = set(train_df["stroke_id"]) & set(test_df["stroke_id"])
    assert not overlap, f"stroke leaked across train/test: {overlap}"
    return train_df, test_df


def build_feature_matrix(df: pd.DataFrame, z_cols=("kappa_t",)):
    """X = [z_t (vector-ready, z_cols), u_t, dir_t]; dZ = dkappa (scalar for
    now; extend z_cols + a matching dZ builder together if the vision
    pipeline emits vector state later -- see README.md)."""
    X = np.column_stack([df[c].to_numpy(dtype=float) for c in z_cols] +
                         [df["u_t"].to_numpy(dtype=float), df["dir_t"].to_numpy(dtype=float)])
    dZ = df["dkappa"].to_numpy(dtype=float).reshape(-1, 1)
    return X, dZ


class Standardizer:
    """Fit on TRAIN data only, applied to both train and test -- avoids
    leaking test statistics into the model input scaling."""

    def __init__(self):
        self.mean_ = None
        self.std_ = None

    def fit(self, X):
        self.mean_ = X.mean(axis=0)
        self.std_ = X.std(axis=0)
        self.std_[self.std_ < 1e-12] = 1.0
        return self

    def transform(self, X):
        if self.mean_ is None:
            raise RuntimeError("Standardizer.transform called before fit")
        return (X - self.mean_) / self.std_

    def fit_transform(self, X):
        return self.fit(X).transform(X)

    def inverse_transform(self, X):
        return X * self.std_ + self.mean_
