"""The analysis schema: one row = one non-overlapping 60 s interval.

Created: 2026-09-03
Last updated: 2026-09-03

Column definitions and the uniqueness key are documented in docs/schema.md. This
module is the machine-readable copy, so the writers and the validator cannot drift
from the document.
"""

from __future__ import annotations

import pandas as pd

# Requested minimum, in the order written.
RMSSD_WINDOW_COLUMNS = [
    "participant_id",
    "site",
    "window_start_utc",
    "window_end_utc",
    "rmssd_ms",
    "n_total_ibi",
    "n_valid_ibi",
    "coverage",
    "wear_percentage",
    "motion_metric",
    "ema_interaction",
    "ema_response_timestamp",
    "phase",
    "source_avro_files",
]

# Audit columns appended after the minimum.
RMSSD_WINDOW_AUDIT_COLUMNS = [
    "window_start_local",
    "included",
    "exclude_reason",
    "detector",
    "run_id",
]

RMSSD_WINDOW_KEY = ["participant_id", "window_start_utc"]
RMSSD_WINDOW_SORT = ["participant_id", "window_start_utc"]

IBI_COLUMNS = ["participant_id", "segment", "onset_utc", "ibi_s", "valid", "reject_reason"]
IBI_KEY = ["participant_id", "segment", "onset_utc"]

BASELINE_COLUMNS = [
    "participant_id", "n_windows_total", "n_windows_valid",
    "baseline_mean_ms", "baseline_sd_ms", "baseline_median_ms",
    "n_excluded_lowcover", "n_excluded_motion", "n_excluded_unworn",
]
BASELINE_KEY = ["participant_id"]

SPIKE_EPISODE_COLUMNS = [
    "participant_id", "direction", "threshold_n", "start_utc", "end_utc",
    "duration_min", "n_windows", "mean_rmssd_ms", "min_rmssd_ms", "max_rmssd_ms",
    "baseline_mean_ms", "baseline_sd_ms", "deviation_sd",
]
SPIKE_EPISODE_KEY = ["participant_id", "direction", "threshold_n", "start_utc"]

PHASES = {"pre_robot", "robot", "post_robot", "baseline", "unassigned"}

WINDOW_LENGTH_S = 60


def validate_rmssd_windows(df: pd.DataFrame, *, window_length_s: int = WINDOW_LENGTH_S) -> pd.DataFrame:
    """Structural checks on the analysis table. Raises on any violation.

    Checks that matter scientifically, not just typing:

    * every window is exactly ``window_length_s`` long;
    * windows for one participant do not overlap — the correction this whole
      rebuild exists for (docs/rmssd_windowing_audit.md);
    * ``n_valid_ibi <= n_total_ibi`` and coverage is a fraction;
    * ``phase`` is drawn from the known vocabulary.
    """
    missing = [c for c in RMSSD_WINDOW_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(f"rmssd_windows missing columns: {missing}")
    if df.empty:
        return df

    start = pd.to_datetime(df["window_start_utc"], utc=True)
    end = pd.to_datetime(df["window_end_utc"], utc=True)

    lengths = (end - start).dt.total_seconds()
    if not (lengths == window_length_s).all():
        raise ValueError(
            f"window length must be exactly {window_length_s}s; "
            f"found {sorted(set(lengths.unique()))[:5]}"
        )

    # Non-overlap: within a participant, each window must start no earlier than
    # the previous window's end.
    ordered = df.assign(_s=start, _e=end).sort_values(["participant_id", "_s"])
    prev_end = ordered.groupby("participant_id")["_e"].shift()
    overlapping = ordered["_s"] < prev_end
    if overlapping.any():
        first = ordered.loc[overlapping, ["participant_id", "_s"]].head(3).to_dict("records")
        raise ValueError(f"overlapping windows detected (must be non-overlapping): {first}")

    if (df["n_valid_ibi"] > df["n_total_ibi"]).any():
        raise ValueError("n_valid_ibi exceeds n_total_ibi")
    cov = df["coverage"].dropna()
    if ((cov < 0) | (cov > 1)).any():
        raise ValueError("coverage must lie in [0, 1]")

    bad_phase = sorted(set(df["phase"].dropna()) - PHASES)
    if bad_phase:
        raise ValueError(f"unknown phase value(s): {bad_phase}; known: {sorted(PHASES)}")

    return df
