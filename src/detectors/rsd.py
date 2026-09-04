"""RSD — rolling-standardised derivative peak detection (sensitivity analysis).

Created: 2026-09-03
Last updated: 2026-09-03

Port of ``~/Documents/empatica-hrv-pipeline/utils/rsd.py`` (Murphy, DePaul 2025).
Five-point fiducial sequence ``onset -> a-peak -> u-peak -> b-trough -> systolic``
on a PPG-APG composite; intervals are taken **onset to onset**, unlike ADT's
peak-to-peak, so the two are not interchangeable without re-deriving intervals.

Carried over unchanged in structure, with two things that must not be inherited
silently: ``prominence`` was tuned per participant on five DePaul participants and
has no established transfer to SAR or to Clemson hardware, and the gap-splitting
sample rate is fixed to that study's 64 Hz device. Both become config values here.
"""

from __future__ import annotations

import numpy as np


def detect_beats(signal, timestamps_s, fs: float, *, prominence: float = 0.5,
                 min_ibi_s: float = 0.33, max_ibi_s: float = 1.5) -> np.ndarray:
    """Beat times (seconds, at pulse onsets) from a preprocessed PPG signal."""
    raise NotImplementedError("RSD port not implemented — audit/architecture phase")
