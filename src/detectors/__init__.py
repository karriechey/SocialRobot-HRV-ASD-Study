"""Peak detectors behind one interface, selected by ``peak_detector`` in config.

Created: 2026-09-03
Last updated: 2026-09-03

Every detector exposes::

    detect_beats(signal, timestamps_s, fs, **params) -> np.ndarray  # beat times, s

so the primary/sensitivity comparison is a config change, not a code change.
Which fiducial the beat time refers to differs by detector and is recorded in the
output ``detector`` column: ADT returns systolic peaks, RSD returns pulse onsets.
See docs/detector_comparison_adt_rsd.md.
"""

from __future__ import annotations


def get_detector(name: str):
    """Return the ``detect_beats`` callable for ``name`` (``adt`` | ``rsd``)."""
    if name == "adt":
        from src.detectors import adt
        return adt.detect_beats
    if name == "rsd":
        from src.detectors import rsd
        return rsd.detect_beats
    raise ValueError(f"unknown peak_detector {name!r}; expected 'adt' or 'rsd'")
