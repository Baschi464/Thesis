"""
schema.py -- the transitions-table contract (gp_code_handoff.md SS2).

Defines the canonical columns for a `transitions.parquet`/`.csv` and
validates a loaded DataFrame against them. No real data exists yet (see
README.md / TODO-REAL-DATA.md) -- this is the schema real recordings must
conform to once the vision+recording pipeline exists; synth.py is the only
producer of conforming data until then.

SCHEMA EXTENSION beyond the literal gp_code_handoff.md SS2 list:
`stroke_id` is required here even though SS2's column list doesn't include
it, because stroke-wise splitting (SS8, "never random rows") needs to know
which rows belong to the same continuous stroke. Real upstream data will
need to emit this too (e.g. derived from contiguous commanded-motion
segments in commands.csv) -- see TODO-REAL-DATA.md. If a loaded table
lacks it, data.py derives a best-effort stroke_id from contiguous runs of
constant (session_id, actuator, regime, dir_t) -- see data.py::_infer_stroke_id.
"""

from dataclasses import dataclass, fields
from typing import Optional

import numpy as np
import pandas as pd

REQUIRED_COLUMNS = {
    "session_id": "object",
    "actuator": "object",
    "t_host": "float64",
    "dt": "float64",
    "kappa_t": "float64",
    "kappa_tp1": "float64",
    "dkappa": "float64",
    "u_t": "float64",
    "u_tp1": "float64",
    "dir_t": "int64",
    "regime": "object",
    "kappa0": "float64",
    "meas_noise_sd": "float64",
    "out_of_plane": "bool",
    "quality": "float64",
}

# Not in gp_code_handoff.md SS2's literal list -- see module docstring.
OPTIONAL_COLUMNS = {
    "stroke_id": "object",
}

ALL_COLUMNS = {**REQUIRED_COLUMNS, **OPTIONAL_COLUMNS}


class SchemaError(ValueError):
    pass


class CrossSessionError(ValueError):
    """Raised when transitions from multiple session_ids are pooled without
    an explicit --allow-cross-session flag + a home-alignment mapping (see
    gp_code_handoff.md SS2 NOTE: step counts `u` are only comparable within
    one session -- no limit switches, home is set manually per session)."""


@dataclass
class Transition:
    """One row of the transitions table -- used for synth.py's row-builder
    and for documenting the contract in code (not the hot path; data.py
    operates on the DataFrame directly for performance)."""
    session_id: str
    actuator: str
    t_host: float
    dt: float
    kappa_t: float
    kappa_tp1: float
    dkappa: float
    u_t: float
    u_tp1: float
    dir_t: int
    regime: str
    kappa0: float
    meas_noise_sd: float
    out_of_plane: bool
    quality: float
    stroke_id: Optional[str] = None

    def as_row(self):
        return {f.name: getattr(self, f.name) for f in fields(self)}


def validate_transitions(df: pd.DataFrame, require_stroke_id: bool = False) -> pd.DataFrame:
    """Validate columns/dtypes/value ranges. Returns a normalized copy
    (consistent dtypes, stroke_id added as NaN if absent and not required).
    Raises SchemaError with a specific message on any violation -- never
    silently coerces bad data into something plausible-looking.
    """
    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        raise SchemaError(f"transitions table missing required columns: {missing}")

    if "stroke_id" not in df.columns:
        if require_stroke_id:
            raise SchemaError("stroke_id column required but absent -- "
                               "call data.py::_infer_stroke_id first or pass require_stroke_id=False")
        df = df.copy()
        df["stroke_id"] = np.nan
    else:
        df = df.copy()

    for col in ("kappa_t", "kappa_tp1", "dkappa", "u_t", "u_tp1", "kappa0", "meas_noise_sd", "quality", "dt", "t_host"):
        df[col] = df[col].astype("float64")
    df["dir_t"] = df["dir_t"].astype("int64")
    df["out_of_plane"] = df["out_of_plane"].astype("bool")

    if not np.isin(df["dir_t"].unique(), [-1, 0, 1]).all():
        raise SchemaError(f"dir_t must be in {{-1,0,1}}, found {sorted(df['dir_t'].unique())}")

    if (df["quality"] < 0).any() or (df["quality"] > 1).any():
        raise SchemaError("quality must be in [0, 1]")

    if (df["dt"] <= 0).any():
        raise SchemaError("dt must be > 0 for every transition")

    resid = (df["kappa_tp1"] - df["kappa_t"] - df["dkappa"]).abs()
    if (resid > 1e-6).any():
        bad = int((resid > 1e-6).sum())
        raise SchemaError(f"dkappa != kappa_tp1 - kappa_t for {bad} row(s) -- data corruption or unit mismatch")

    return df


def check_single_session(df: pd.DataFrame, allow_cross_session: bool, home_alignment: Optional[dict] = None):
    """Cross-session guard (gp_code_handoff.md SS2 NOTE). u is only
    comparable within one session_id (no limit switches -> per-session
    manual home). Raises CrossSessionError unless either only one session
    is present, or the caller explicitly opts in with a home_alignment
    mapping covering every session present.
    """
    sessions = df["session_id"].unique().tolist()
    if len(sessions) <= 1:
        return
    if not allow_cross_session:
        raise CrossSessionError(
            f"transitions span {len(sessions)} sessions {sessions} -- u (step counts) "
            "is only comparable within one session (no limit switches; home is set "
            "manually per session, see gp_code_handoff.md SS2). Pass "
            "allow_cross_session=True with a home_alignment mapping to override."
        )
    if home_alignment is None or not all(s in home_alignment for s in sessions):
        missing = [s for s in sessions if home_alignment is None or s not in home_alignment]
        raise CrossSessionError(
            f"allow_cross_session=True but home_alignment is missing an entry for "
            f"session(s) {missing} -- every session present needs an explicit "
            "home-alignment offset before u can be pooled across sessions."
        )
