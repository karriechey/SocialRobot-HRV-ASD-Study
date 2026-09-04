"""Per-participant resting baseline RMSSD.

Created: 2026-09-03
Last updated: 2026-09-03

Mean and SD over quality-gated baseline windows, one convention throughout
(``ddof=1``), written to ``results/baseline_stats.csv`` and **read** by the spike
stage.

Two failures in the original analysis this is written against:

* Two baseline notebooks with different answers — one using ``ddof=1`` and keeping
  zeros, the other dropping ``RMSSD == 0`` and using ``np.std`` (``ddof=0``) in one
  cell and ``ddof=1`` in another. Which produced the published numbers is unknown.
* The resulting statistics were hard-coded as literals into the spike notebook,
  with a single participant selected at the top, so every participant's file could
  be labelled against one participant's baseline.

No statistic is transcribed by hand between stages here.

The baseline is also where the windowing correction bites hardest: an SD computed
from beat-level rolling values is far smaller than one computed from independent
60 s windows, which makes ``mean - N*SD`` less extreme and flags more windows than
the stated method would (docs/rmssd_windowing_audit.md).
"""

from __future__ import annotations

import pandas as pd


def compute_baseline_stats(windows: pd.DataFrame) -> pd.DataFrame:
    """One row per participant, over ``included`` baseline windows only."""
    raise NotImplementedError("not implemented — audit/architecture phase")
