# `scripts/`

Created: 2026-09-03
Last updated: 2026-09-03

Headless runners, one per stage. Each is a thin argument-parsing wrapper around
`src/` — no analysis logic lives here, so a notebook and a script always compute
the same thing.

| Script | Stage | Reads | Writes |
|---|---|---|---|
| `1_ingest_avro.py` | AVRO -> sensor tables + per-minute biomarkers | `data/raw/` | `data/interim/{pid}/` |
| `2_detect_beats.py` | preprocess + peak detection + IBI quality flags | `data/interim/` | `results/ibi/{pid}_ibi.csv` |
| `3_compute_rmssd.py` | non-overlapping 60 s windows | `results/ibi/` | `results/rmssd_windows.csv` |
| `4_baseline_stats.py` | quality-gated per-participant baseline | `results/rmssd_windows.csv` | `results/baseline_stats.csv` |
| `5_detect_spikes.py` | spike labelling + episodes | windows + baseline | `results/spike_episodes.csv` |
| `6_validate_detector.py` | ADT and RSD vs. Empatica per-minute pulse rate | `results/ibi/`, biomarkers | `results/validation/` |

Common flags: `--participant`, `--config`, `--detector {adt,rsd}`, `--dry-run`.

Every run writes `results/manifests/{run_id}.json`. Re-running a stage over
identical inputs replaces its outputs byte-for-byte; nothing appends
(`docs/idempotency.md`).

`6_validate_detector.py` is stage zero in practice: neither detector has ever been
compared against Empatica's own pulse-rate biomarker (`docs/adt_audit.md`), and
that comparison is the tie-breaker for the ADT-vs-RSD decision.
