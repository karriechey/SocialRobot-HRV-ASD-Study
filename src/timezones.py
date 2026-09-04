"""Timezone handling. UTC is canonical; local time is a display projection.

Created: 2026-09-03
Last updated: 2026-09-03

Rules are stated in docs/timezone_policy.md. This module is the only place
conversions happen, and it contains no timezone literal — every zone arrives as an
argument sourced from config/sites.yaml or config/participants.csv.

The regression this exists to prevent: the original pipeline hard-coded
``America/Chicago`` in every conversion, including the loop over Clemson data, so
every Clemson local timestamp was an hour off.
"""

from __future__ import annotations

import pandas as pd

UTC = "UTC"


class NaiveTimestampError(ValueError):
    """A naive timestamp reached code that requires tz-aware input."""


def require_utc(series: pd.Series, name: str = "timestamp") -> pd.Series:
    """Assert a datetime Series is tz-aware UTC. Raises otherwise.

    Called at the entry of anything that does timestamp arithmetic, so a naive
    value cannot silently propagate into a join or a window boundary.
    """
    if not pd.api.types.is_datetime64_any_dtype(series):
        raise NaiveTimestampError(f"{name} is not a datetime series (got {series.dtype})")
    tz = getattr(series.dtype, "tz", None)
    if tz is None:
        raise NaiveTimestampError(f"{name} is timezone-naive; localise it at ingestion")
    if str(tz) != UTC:
        raise NaiveTimestampError(f"{name} is {tz}, expected UTC")
    return series


def from_unix_us(values) -> pd.Series:
    """Empatica AVRO microsecond timestamps -> tz-aware UTC.

    ``timestampStart`` is already UTC, so there is no localisation step and no
    site information is needed here.
    """
    return pd.to_datetime(pd.Series(values), unit="us", utc=True)


def localize_naive_local(values, tz: str, *, name: str = "ema_response_timestamp") -> pd.Series:
    """Naive local wall-clock values -> tz-aware UTC, via the given zone.

    Used for EMA exports, which carry naive local times. DST is resolved by the tz
    database, and both edge cases are refused rather than guessed:

    * ``nonexistent="raise"`` — a time inside the spring-forward gap did not occur.
    * ``ambiguous="raise"``   — a time inside the fall-back hour occurred twice.

    Either raise means a data problem to resolve and record by hand. The caller
    quarantines the row; it is never shifted or dropped silently.
    """
    local = pd.to_datetime(pd.Series(values))
    if getattr(local.dtype, "tz", None) is not None:
        raise ValueError(f"{name} is already tz-aware; this function expects naive local input")
    try:
        aware = local.dt.tz_localize(tz, nonexistent="raise", ambiguous="raise")
    except Exception as exc:                       # pandas raises several types here
        raise ValueError(
            f"{name}: could not localise to {tz} (DST gap or ambiguous hour): {exc}"
        ) from exc
    return aware.dt.tz_convert(UTC)


def to_local_display(series: pd.Series, tz: str) -> pd.Series:
    """UTC -> local, for human-readable output columns only.

    The result must never be used for joins, comparisons, or arithmetic. It exists
    so a reader can see 'that was 3pm for the participant'.
    """
    return require_utc(series).dt.tz_convert(tz)
