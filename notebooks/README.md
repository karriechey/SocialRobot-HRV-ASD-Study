# `notebooks/`

Created: 2026-09-03
Last updated: 2026-09-03

Notebooks are drivers and narrative, not implementation. Each one imports from
`src/`, calls a handful of functions, and shows figures and tables. A notebook
cell that defines analysis logic belongs in `src/` instead — that is the single
structural change carried over from the previous Empatica HRV pipeline, and the
reason the original SAR analysis has two baseline notebooks that disagree.

Planned, mirroring `scripts/`:

- `0_project_log.ipynb` — running record of decisions and results
- `1_ingest_avro.ipynb`
- `2_detect_beats.ipynb`
- `3_compute_rmssd.ipynb`
- `4_baseline_stats.ipynb`
- `5_detect_spikes.ipynb`
- `6_validate_detector.ipynb` — ADT and RSD against Empatica pulse rate
- `7_threshold_sensitivity.ipynb` — spike counts across N, coverage, and detector

Swetha's original notebooks are **not** copied here and are not modified. They
stay where they are as the reference for what the published analysis did.
