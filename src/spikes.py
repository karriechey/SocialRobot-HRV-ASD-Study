"""Spike detection against the personal baseline.

Created: 2026-09-03
Last updated: 2026-09-03

A spike is a run of consecutive 60 s windows beyond ``mean +/- N*SD`` of the
participant's own baseline, for N in {1, 2, 3}. Because the windows are genuinely
non-overlapping minutes, ``duration_min`` is a duration in minutes — in the
original implementation ``Spike_Duration`` was ``transform('count')`` over
beat-level rows, so a one-minute spike reported roughly 72.

Windows with ``rmssd_ms = NaN`` are missing, not non-spikes: they break episode
continuity and are never counted as flagged.

Both directions are computed. The original flagged only downward deviations; which
the manuscript reports is unresolved (docs/open_questions.md item 9).
"""

from __future__ import annotations

import pandas as pd


def label_windows(windows: pd.DataFrame, baseline: pd.DataFrame, params: dict) -> pd.DataFrame:
    """Add ``spike_down_N`` / ``spike_up_N`` boolean columns per threshold."""
    raise NotImplementedError("not implemented — audit/architecture phase")


def build_episodes(labeled: pd.DataFrame, baseline: pd.DataFrame, params: dict) -> pd.DataFrame:
    """One row per contiguous run of flagged windows."""
    raise NotImplementedError("not implemented — audit/architecture phase")
