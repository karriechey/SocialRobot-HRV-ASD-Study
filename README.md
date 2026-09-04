# SocialRobot-HRV-ASD-Study

Created: 2026-09-03
Last updated: 2026-09-03

Rebuilt analysis pipeline for the SAR autism paper: Empatica EmbracePlus BVP ->
inter-beat intervals -> RMSSD over non-overlapping 60-second windows -> personal
baseline -> HRV spikes, joined to EMA responses across two sites (DePaul, Clemson).

**Current phase: audit and architecture.** No stage is implemented and nothing has
been run on the full dataset. `src/` carries the working configuration, timezone,
window-grid, schema and I/O layers; the analysis stages are documented interfaces
that raise `NotImplementedError`.

## Layout

```
src/          reusable logic — everything the pipeline actually does
scripts/      headless per-stage runners (thin wrappers over src/)
notebooks/    drivers and narrative (no logic)
config/       participants.csv, sites.yaml, pipeline.yaml
docs/         audit findings, schema, policies, open questions
results/      generated outputs (gitignored)
data/         raw research data, ~17 GB (gitignored, read-only)
```

## Participant identity

The raw participant folders under `data/` are named with real first names. The
repository therefore splits its registry in two:

* `config/participants.csv` — **committed**, analysis IDs only, `wearable_folder`
  left blank
* `config/participants.local.csv` — **gitignored**, maps an ID to its real folder

`src/config.py` raises if the committed file carries a path, so a name cannot
reach a commit by habit. See `config/participants.README.md`. Nothing under
`data/` is trackable, and `.gitignore` also refuses `*.csv`, `*.xlsx` and `*.avro`
anywhere in the tree by default.

## Read first

| Document | What it settles |
|---|---|
| `docs/pipeline_comparison.md` | Stage-by-stage comparison of the previous Empatica pipeline and Swetha's SAR pipeline, with the recommended implementation and the definite bugs found in each |
| `docs/rmssd_windowing_audit.md` | The manuscript says non-overlapping 60 s; the code computes a per-beat rolling window. Confirmed, quantified, and its consequences traced |
| `docs/adt_audit.md` | ADT parameters, refractory logic, the index-0 fabricated interval, and the absence of any validation against Empatica pulse rate |
| `docs/detector_comparison_adt_rsd.md` | How RSD differs from ADT; the ADT-primary / RSD-sensitivity plan and what must be settled before it is final |
| `docs/schema.md` | One row = one true non-overlapping 60 s interval |
| `docs/timezone_policy.md` | UTC canonical, site-driven local display, DST via `zoneinfo` |
| `docs/idempotency.md` | Re-running produces identical outputs; uniqueness keys and atomic writes |
| `docs/open_questions.md` | Everything unresolved, including what blocks final numbers |

## Ground rules

- Raw research data is read-only. No stage sorts, rewrites, or de-duplicates a
  source file in place.
- Swetha's original notebooks and `ADT.py` are never modified, and are not copied
  into this repo.
- Participant identity lives only in `config/participants.csv`. No names, no
  absolute paths, no hard-coded date ranges in code.
- Blanks stay blank. Nothing unknown is filled in with a plausible value.
- No participant name appears in any committed file, including documentation.
