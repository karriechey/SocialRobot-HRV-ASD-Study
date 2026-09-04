# `tests/`

Created: 2026-09-03
Last updated: 2026-09-03

Tests that must exist before any number is trusted:

| Test | Asserts |
|---|---|
| `test_windows.py` | the grid is contiguous, half-open, exactly 60 s, and non-overlapping; an IBI lands in the window containing its closing beat |
| `test_schema.py` | `validate_rmssd_windows` rejects overlapping windows, wrong-length windows, `n_valid_ibi > n_total_ibi`, and unknown `phase` values |
| `test_timezones.py` | one UTC instant renders to different local wall-clock times for a DePaul and a Clemson participant and round-trips to the same UTC; a DST-gap and an ambiguous local time both raise; naive input to a UTC-requiring function raises |
| `test_idempotency.py` | running a stage twice over a fixture produces byte-identical files; a duplicate key raises `DuplicateRowsError` |
| `test_hrv.py` | neurokit2 RMSSD and the closed-form expression agree on clean input; a window below `min_valid_ibi` or `min_coverage` returns `NaN`; no successive difference is taken across a rejected beat |
| `test_config.py` | duplicate `participant_id`, unknown site, unknown timezone, and an exclusion without a reason all raise |
| `test_no_paths_committed.py` | a non-blank `wearable_folder` in the committed `participants.csv` raises; a local row naming an unknown participant raises; a missing local file is tolerated |
| `test_rolling_vs_nonoverlapping.py` | the beat-level rolling diagnostic emits ~HR values per minute while the analysis grid emits one — a regression guard on the central correction |
