# Idempotent output policy

Created: 2026-09-03
Last updated: 2026-09-03

**Requirement.** Running any stage twice over identical raw inputs produces
byte-identical processed outputs. No duplicated rows, ever.

The original pipeline violated this at stage 1: outputs were opened with
`mode = 'ab' if append_mode and os.path.exists(file_path) else 'wb'`, so a re-run
appended a second copy of every sample. The duplicate-detection and in-place
re-sorting helpers in the same notebook exist because that happened.

## Rules

1. **Never append to a processed artifact.** Every stage computes its full output
   for the scope it was given, then replaces the file.
2. **Write atomically.** Write to `path.tmp` in the same directory, `flush` +
   `os.replace(tmp, path)`. A crashed run leaves either the previous complete file
   or nothing — never a half file that the next stage happily reads.
3. **Deterministic ordering.** Fixed column order and a fixed sort key before
   every write (`(participant_id, window_start_utc)` for windows). Float
   formatting fixed via a single `to_csv(float_format=...)` setting.
4. **Uniqueness key enforced before write.** For each artifact:

   | Artifact | Key |
   |---|---|
   | `results/rmssd_windows.csv` | `(participant_id, window_start_utc)` |
   | `results/ibi/{pid}_ibi.csv` | `(segment, onset_utc)` |
   | `results/baseline_stats.csv` | `(participant_id)` |
   | `results/spike_episodes.csv` | `(participant_id, direction, threshold_n, start_utc)` |

   A duplicate raises `DuplicateRowsError` naming the offending keys. It is not
   de-duplicated silently, because a duplicate means two runs disagreed about
   something and that needs to be looked at.
5. **Per-participant scope, whole-file replace.** A run for one participant
   rewrites that participant's rows: the existing file is read, that participant's
   rows are dropped, the new rows are concatenated, the key check runs, and the
   file is replaced atomically. This is a replace-by-key, not an append.
6. **Never write back over an input.** Stage inputs and outputs live at different
   paths. (The original stage 5 read `HRV.xlsx`, filtered it to 12 minutes, and
   wrote the result back to `HRV.xlsx`.)
7. **Raw data is read-only.** No stage sorts, rewrites, de-duplicates or otherwise
   touches anything under the raw data root. `sort_csv_by_timestamp()`-style
   in-place mutation of source files is not used.
8. **Run manifest.** Every write emits `results/manifests/{run_id}.json` recording
   the config hash, the code revision, the input file list with sizes and mtimes,
   the output row counts, and the UTC start/end. Two runs whose manifests match on
   config hash and input list must produce identical outputs; a helper compares
   two runs and reports the first differing column.

## Checks provided

- `src/io_utils.py::assert_unique(df, keys, name)` — raises on duplicate keys.
- `src/io_utils.py::write_table(df, path, keys, sort_by, columns)` — sorts,
  reorders, checks uniqueness, writes atomically.
- `src/io_utils.py::upsert_participant_rows(df, path, participant_id, ...)` —
  replace-by-key for single-participant re-runs.
- A test that runs a stage twice over a fixture and asserts identical bytes.
