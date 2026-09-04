# SAR analysis data schema

Created: 2026-09-03
Last updated: 2026-09-03

## Grain

**One row = one true non-overlapping 60-second interval, for one participant.**

The interval grid is built on UTC, anchored at the participant's segment start
floored to the minute, and advanced by exactly 60 s. Windows do not overlap, are
not centered on beats, and are not skipped when empty: a minute with no usable
beats is still emitted with `rmssd_ms = NaN` so that timeline coverage is
auditable rather than implied by absence.

Uniqueness key: **`(participant_id, window_start_utc)`**. Enforced before write.

## `results/rmssd_windows.csv`

| Column | Type | Units / format | Definition |
|---|---|---|---|
| `participant_id` | string | e.g. `DP01` | From `config/participants.csv`. Never a real name. |
| `site` | string | `depaul` \| `clemson` | From `config/participants.csv`. |
| `window_start_utc` | timestamp | ISO 8601, tz-aware, `+00:00` | Inclusive start of the interval. |
| `window_end_utc` | timestamp | ISO 8601, tz-aware, `+00:00` | Exclusive end. Always `window_start_utc + 60 s`. |
| `rmssd_ms` | float | ms | RMSSD over the beats whose IBI closes inside the interval, computed per continuous valid run and pooled by difference count. `NaN` when the minimum-beat or coverage requirement fails. |
| `n_total_ibi` | int | count | Intervals closing inside the window, before validity filtering. |
| `n_valid_ibi` | int | count | Of those, intervals passing physiological bounds + Mateo–Laguna + neighbour invalidation. |
| `coverage` | float | 0–1 | `sum(valid IBI seconds) / 60`. Fraction of the minute actually accounted for by accepted beats. |
| `wear_percentage` | float | 0–100 | Empatica `wearing-detection` biomarker for the matching minute. `NaN` if absent. |
| `motion_metric` | float | g | Empatica `accelerometers-std` biomarker for the matching minute. `NaN` if absent. Nullable by design — Clemson downloads may not include it. |
| `ema_interaction` | string | categorical / nullable | EMA-reported interaction label attached to this window, or null if no EMA response maps here. Vocabulary to be fixed once the SAR EMA codebook is located. |
| `ema_response_timestamp` | timestamp | ISO 8601, tz-aware UTC, nullable | UTC instant of the EMA response that produced `ema_interaction`. Original naive local value is localised by site before conversion. |
| `phase` | string | categorical | Study phase for this window: `pre_robot`, `robot`, `post_robot`, `baseline`, `unassigned`. Derived from `robot_delivery` boundaries in `config/participants.csv`. `unassigned` where boundaries are unknown — never guessed. |
| `source_avro_files` | string | `;`-separated basenames | Every AVRO file contributing at least one BVP sample to this window. Provenance for reproducing a single row. |

### Derived / audit columns (written, not part of the requested minimum)

| Column | Purpose |
|---|---|
| `window_start_local` | Display projection only, via the site timezone. Never used for joins or arithmetic. |
| `included` | Boolean: passed the analysis quality gate (`n_valid_ibi >= min_beats` and `coverage >= min_coverage` and, for baseline windows, the wear and motion gates). |
| `exclude_reason` | Human-readable reason when `included` is False. Empty otherwise. |
| `detector` | `adt` \| `rsd`. Which peak detector produced the beats. |
| `run_id` | Identifier of the run manifest that wrote this row. |

## Sort and column order

Rows sorted by `(participant_id, window_start_utc)`; columns written in the order
above. Both are fixed so that two runs on identical inputs produce byte-identical
files.

## Companion artifacts

| Path | Grain |
|---|---|
| `results/ibi/{participant_id}_ibi.csv` | one row per detected beat: `segment, onset_utc, ibi_s, valid, reject_reason` |
| `results/baseline_stats.csv` | one row per participant: `participant_id, n_windows_total, n_windows_valid, baseline_mean_ms, baseline_sd_ms, baseline_median_ms, n_excluded_*` |
| `results/spike_episodes.csv` | one row per episode: `participant_id, direction, threshold_n, start_utc, end_utc, duration_min, n_windows, mean_rmssd_ms, deviation_sd` |
| `results/manifests/{run_id}.json` | config hash, code revision, input file list, row counts, timestamp |

`baseline_stats.csv` is **read** by the spike stage. No statistic is ever
transcribed by hand between stages.
