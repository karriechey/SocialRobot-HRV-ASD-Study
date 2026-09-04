"""Window-level quality gate: coverage, wear, motion.

Created: 2026-09-03
Last updated: 2026-09-03

Joins the Empatica per-minute biomarkers onto each 60 s window and decides which
windows are trustworthy. Neither source pipeline for SAR applied any of this — the
accelerometer was converted and never read, and wearing detection was never read
at all, so the published baselines pooled off-wrist, high-motion and sleeping
minutes together with resting ones.

Gates are applied to the **baseline**; on task windows the metrics are carried but
not applied, so the filter can be varied in sensitivity analysis without
recomputing HRV. ``exclude_reason`` is written for every excluded window.

All thresholds are provisional, inherited from a different study, and must be
re-justified for SAR (docs/open_questions.md item 7).
"""

from __future__ import annotations

import pandas as pd


def attach_biomarkers(windows: pd.DataFrame, wear: pd.DataFrame, motion: pd.DataFrame
                      ) -> pd.DataFrame:
    """Join ``wear_percentage`` and ``motion_metric`` onto each window by minute.

    Both are nullable: a Clemson download may not include the per-minute
    biomarkers at all, in which case the columns stay NaN and the gate that needs
    them is reported as unavailable rather than silently passing.
    """
    raise NotImplementedError("not implemented — audit/architecture phase")


def apply_gate(windows: pd.DataFrame, params: dict, *, is_baseline: bool) -> pd.DataFrame:
    """Add ``included`` and ``exclude_reason``."""
    raise NotImplementedError("not implemented — audit/architecture phase")
