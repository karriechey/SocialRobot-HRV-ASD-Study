"""ADT — adaptive-threshold systolic peak detection (primary, provisionally).

Created: 2026-09-03
Last updated: 2026-09-03

Wrapper around the original study's implementation so the corrected pipeline can
keep its beat detection identical to the published analysis. The original file
(``ADT.py``) is NOT modified and NOT vendored into this repo during the audit
phase; it is referenced so a decision can be recorded before anything is copied.

Two corrections are pending a decision (docs/adt_audit.md, docs/open_questions.md
item 6), both behind the ``adt:`` block in config/pipeline.yaml:

1. ``drop_index_zero`` — the detector initialises ``fiducial_points = [0]``, which
   is the first sample of the record, not a beat. It is returned in the output, so
   the first real beat produces a fabricated interval ``ts[first_peak] - ts[0]``
   and contaminates the first two successive differences of every processed file.
2. Output-side physiological bounds. The class constants 0.350-1.200 s gate only
   the internal refractory estimate; the returned peaks are unfiltered.

Applying either makes the primary pipeline no longer literally identical to the
original detector. That is a methods statement to make explicitly, either way.
"""

from __future__ import annotations

import numpy as np


def detect_beats(signal, timestamps_s, fs: float, *, drop_index_zero: bool = True
                 ) -> np.ndarray:
    """Beat times (seconds, at systolic peaks) from a preprocessed PPG signal."""
    raise NotImplementedError("ADT wrapper not implemented — audit/architecture phase")
