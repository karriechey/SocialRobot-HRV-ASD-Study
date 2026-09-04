"""BVP preprocessing shared by both peak detectors.

Created: 2026-09-03
Last updated: 2026-09-03

Both detectors receive the *same* preprocessed signal, so the ADT-vs-RSD
sensitivity analysis isolates the detector rather than confounding it with a
different filter chain.

Order: gap-split -> (optional inversion) -> cubic-spline upsample -> Butterworth
bandpass (zero-phase) -> rolling standardisation. Parameters come from
config/pipeline.yaml.

The gap split is not optional. The original pipeline fitted one ``CubicSpline``
from ``min(ts)`` to ``max(ts)``, so every watch-off period and file-boundary gap
was filled with fabricated waveform that then had beats detected on it.
"""

from __future__ import annotations

import numpy as np


def split_on_gaps(timestamps_s, values, original_fs: float, gap_factor: float = 5.0):
    """Yield contiguous ``(ts, values)`` runs, breaking wherever spacing exceeds
    ``gap_factor / original_fs``. No interpolation ever crosses a gap."""
    raise NotImplementedError("not implemented — audit/architecture phase")


def upsample_cubic(timestamps_s, values, new_fs: float):
    """Cubic-spline resample one contiguous run onto a uniform ``new_fs`` grid."""
    raise NotImplementedError("not implemented — audit/architecture phase")


def bandpass(values, fs: float, low: float, high: float, order: int):
    """Zero-phase Butterworth bandpass."""
    raise NotImplementedError("not implemented — audit/architecture phase")


def rolling_standardize(values, fs: float, window_s: float):
    """Centered rolling (x - mean) / std, to hold peak amplitude stable through
    motion-induced amplitude drift."""
    raise NotImplementedError("not implemented — audit/architecture phase")
