# Participant configuration

Created: 2026-09-03
Last updated: 2026-09-03

Two files, deliberately split, because this repository lives in the same
directory as the raw data and the raw participant folders are named with real
first names (`data/Clemson/P{n}_P{letter}_{firstname}`)).

| File | Committed? | Holds |
|---|---|---|
| `config/participants.csv` | **yes** | analysis IDs and study metadata only |
| `config/participants.local.csv` | **no — gitignored** | `participant_id` -> real `wearable_folder` path |

`config/participants.local.csv.example` is the committed header-only template;
copy it to `participants.local.csv` and fill it in locally.

The loader merges the two. `wearable_folder` in the committed file must be blank;
a non-blank value raises `ConfigError` unless
`allow_paths_in_committed_config: true` is set in `config/pipeline.yaml`. That
check is the mechanism preventing a name from reaching a commit by habit — it
does not depend on anyone remembering the rule.

## `config/participants.csv` — committed

Header-only template. Nothing is filled in, because none of the values are known
from the audited material and inventing them would produce results that look
complete and are not. Blanks stay blank until answered in
`docs/open_questions.md`.

| Column | Required | Format | Meaning |
|---|---|---|---|
| `participant_id` | yes | short code, e.g. `DP01`, `CU02` | Stable analysis ID. Appears in every output. Never a real name. |
| `site` | yes | `depaul` \| `clemson` | Drives the timezone and any site-level covariate. |
| `wearable_folder` | **leave blank** | — | Supplied by `participants.local.csv`. Present here so the schema is visible; filling it in is what would leak a name. |
| `ema_id` | yes | string | The participant's identifier **in the EMA export**, which is not the same as `participant_id`. Must be an opaque ID, not a name. |
| `timezone` | no | IANA name | Blank inherits from `site` via `config/sites.yaml`. Fill in only for a participant whose data was collected in a different zone from their site. |
| `robot_delivery` | no | `start_local/end_local`, ISO 8601 naive local | Robot delivery boundaries used to derive `phase`. Blank ⇒ `phase = unassigned`. |
| `analysis_include` | yes | `true` \| `false` | Whether the participant enters the analysis. |
| `exclusion_reason` | when `analysis_include=false` | free text | Why. Required non-empty when excluded, so an exclusion is never silent. Must not name the participant. |

## `config/participants.local.csv` — gitignored

| Column | Meaning |
|---|---|
| `participant_id` | must match a row in the committed file |
| `wearable_folder` | path to that participant's Empatica download, relative to `paths.raw_root` |

Loading validates: `participant_id` unique in both files; every local row matches a
committed row; `site` known; `timezone` blank or a valid IANA name;
`analysis_include` parseable; `exclusion_reason` non-empty when excluded. A
malformed row raises rather than being skipped.

A participant with no local row simply has no resolvable data path — the stage
reports it and moves on, rather than guessing a folder.
