"""IBI artifact rejection.

Created: 2026-09-03
Last updated: 2026-09-03

Three stages, in order, from config/pipeline.yaml:

1. **Physiological bounds, two-sided.** The original pipeline rejected only
   ``IBI > 1.15 s``. Nothing rejected short intervals, so split-beat detections
   survived and depressed RMSSD — in exactly the direction the study calls a
   stress spike.
2. **Mateo & Laguna divided-difference rule**, as in the original analysis.
3. **Neighbour invalidation.** A rejected beat corrupts the interval on each side
   of it, so both neighbours are marked invalid too.

Rejected beats are flagged, never dropped. Dropping them would make the surviving
neighbours adjacent and manufacture a successive difference across the gap — an
artifact of the removal, not physiology.

Every rejection carries a ``reject_reason`` so a window's quality is inspectable
rather than inferred from a count.
"""

from __future__ import annotations

import pandas as pd


def physiological_mask(ibi_s, min_s: float, max_s: float):
    """True where the interval is physiologically plausible (two-sided)."""
    raise NotImplementedError("not implemented — audit/architecture phase")


def mateo_laguna_mask(beat_times_s, window_beats: int, xi: float, max_threshold: float):
    """True where the beat passes the Mateo-Laguna abnormal-beat test."""
    raise NotImplementedError("not implemented — audit/architecture phase")


def invalidate_neighbors(valid_mask):
    """Also invalidate the immediate neighbours of every invalid beat."""
    raise NotImplementedError("not implemented — audit/architecture phase")


def flag_ibis(ibi_df: pd.DataFrame, params: dict) -> pd.DataFrame:
    """Add ``valid`` and ``reject_reason``. Nothing is dropped."""
    raise NotImplementedError("not implemented — audit/architecture phase")
