"""Non-overlapping 60-second window construction.

Created: 2026-09-03
Last updated: 2026-09-03

This module is the correction at the centre of the rebuild. The original pipeline
computed HRV with ``df.rolling(on="dt", window="60s", center=True, min_periods=1)``
over a beat-indexed frame, which emits one value per beat — roughly 60-100 values
per minute, adjacent values sharing ~59/60 of their IBIs (measured lag-1
autocorrelation 0.99). The manuscript describes one value per non-overlapping
minute. See docs/rmssd_windowing_audit.md.

Here a window is a half-open UTC interval ``[start, start + 60s)``. An IBI belongs
to the window containing the beat that *closes* it. Every window in the requested
span is emitted, including empty ones, so missing data is visible as a row with
``n_total_ibi = 0`` rather than as an absent row.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from src.timezones import require_utc

WINDOW_LENGTH_S = 60


def window_grid(start_utc: pd.Timestamp, end_utc: pd.Timestamp,
                window_length_s: int = WINDOW_LENGTH_S) -> pd.DataFrame:
    """Half-open, non-overlapping windows covering ``[start_utc, end_utc)``.

    The grid is anchored at ``start_utc`` floored to the minute, so the same
    segment always yields the same window boundaries regardless of when the
    pipeline is run or which participant is processed first.
    """
    if start_utc.tzinfo is None or end_utc.tzinfo is None:
        raise ValueError("window_grid requires tz-aware UTC bounds")

    anchor = start_utc.tz_convert("UTC").floor("min")
    stop = end_utc.tz_convert("UTC")
    starts = pd.date_range(anchor, stop, freq=f"{window_length_s}s", inclusive="left", tz="UTC")
    return pd.DataFrame({
        "window_start_utc": starts,
        "window_end_utc": starts + pd.Timedelta(seconds=window_length_s),
    })


def assign_windows(ibi_df: pd.DataFrame, grid: pd.DataFrame,
                   window_length_s: int = WINDOW_LENGTH_S) -> pd.DataFrame:
    """Attach a window index to each IBI by the time of its closing beat.

    ``ibi_df`` needs ``onset_utc`` (tz-aware UTC, the closing beat of the interval)
    and ``ibi_s``. Beats outside the grid get index -1 and are dropped by callers.
    """
    if ibi_df.empty:
        return ibi_df.assign(window_index=pd.Series(dtype=int))
    require_utc(ibi_df["onset_utc"], "onset_utc")

    anchor = grid["window_start_utc"].iloc[0]
    offset = (ibi_df["onset_utc"] - anchor).dt.total_seconds()
    idx = np.floor(offset / window_length_s).astype("int64")
    idx = idx.where((idx >= 0) & (idx < len(grid)), -1)
    return ibi_df.assign(window_index=idx)
