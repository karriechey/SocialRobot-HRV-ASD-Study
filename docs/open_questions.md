# Open questions

Created: 2026-09-03
Last updated: 2026-09-03

Unresolved items blocking the corrected SAR analysis. Nothing here has been
guessed at or filled in with a placeholder value in code or config — blanks in
`config/participants.csv` stay blank until answered.

Status key: **BLOCKING** (cannot produce final numbers), **NEEDED** (can proceed
with a stated assumption, must be resolved before writing), **OPEN** (decision to
make, no external input required).

---

## 1. Clemson participant mappings — PARTLY RESOLVED, still BLOCKING

The raw data tree contains **five** Clemson participant folders, each named
`P{n}_P{letter}_{name}`, so the study-ID-to-folder mapping is recoverable from
disk. Two identifier schemes are in play (`P2..P6` and `PA..PE`), and Swetha's
code addressed participants positionally as `P2`, `P3`, ... with per-participant
date ranges typed inline — so it is **not** established that her `P2` is the same
person as folder `P2`.

Still needed:
- which of the two schemes the manuscript's participant labels refer to;
- the `ema_id` for each, which is not derivable from the folder tree;
- confirmation that the fifth folder is a real fifth participant and not a
  re-enrollment or a duplicate of an earlier one — two of the five folders carry
  the same first name with a `2` suffix, which is either two different people who
  share a name or one person recorded twice.

Fill into `config/participants.csv` (IDs, `ema_id`) and
`config/participants.local.csv` (folder paths, gitignored).

## 2. Which Clemson EMA ID maps to which of the two named participants — BLOCKING

Two Clemson participants are known by first name only in the working notes; the
EMA export uses opaque IDs. The mapping is not recorded in any audited file. If it
is inverted, every EMA-linked window for both is attached to the wrong person, and
the participant-level results for both are wrong in a way no internal check will
catch.

Complicating it: the raw tree has **two folders whose participant name is the
same**, distinguished only by a numeric suffix. Whichever way the EMA IDs map,
that pair has to be disambiguated first.

Needed: an authoritative statement of the mapping from whoever ran Clemson data
collection, in writing, stored in `config/participants.local.csv` (gitignored) and
never in a committed file.

## 3. Missing robot delivery boundaries — BLOCKING for `phase`

`phase` (`pre_robot` / `robot` / `post_robot`) requires a start and end instant per
participant for the robot delivery. These are not present in any audited file. Two
sub-questions:

- Is a delivery a single contiguous interval per participant, or several sessions?
- Are the recorded times local wall clock (and if so, recorded at which site's
  clock — the participant's site, or the researcher's)?

Until answered, `phase` is written as `unassigned` for the affected windows rather
than inferred from EMA timing or from the shape of the data.

## 4. The fifth excluded DePaul participant — NEEDED

There is a fifth DePaul participant who is excluded. The raw data tree holds
**four** DePaul folders (`DP-P1` .. `DP-P4`), so the fifth participant's wearable
data is not present on this machine at all. Unresolved: their ID, the reason for
exclusion, when the exclusion was decided, whether their raw data still exists
anywhere, and whether it contributed to any number in the current manuscript (in
particular to the baseline statistics). `config/participants.csv` has `analysis_include` and
`exclusion_reason` columns for exactly this; both are blank for now.

Related: `4_detect_spike.ipynb` carries a `participants_stats` dict with P1–P4,
P2's `"std"` left as a syntax-invalid empty value and P2/P3/P4 commented out.
Whether four or five participants were ever analysed together is not determinable
from the code.

## 5. The original analysis dataset — BLOCKING for reproduction

Which files produced the numbers in the manuscript? The audited notebooks write to
absolute paths on the original analyst's Desktop (`/Users/<original analyst>/Desktop/SAR/...`,
`/Users/<original analyst>/Desktop/Clemson data/...`) that are not present on this
machine. Specifically unresolved:

- Where is the raw AVRO tree for both sites now, and is it complete?
- Which of the two baseline notebooks (`3_calculate_mean_std` vs.
  `3_hrv_mean_std`) produced the published baselines? They use different SD
  conventions and different zero-handling and will not agree.
- The shipped converter reads `P3-<name>` and writes to `P4-<different name>`
  (see `docs/pipeline_comparison.md`, bug 1). Were any published CSVs produced by
  that code path, and if so under which participant label?
- Are the intermediate `HRV.xlsx` files still available, given that stage 5
  overwrote its inputs in place?

Without an answer, the corrected pipeline can be *built* and *run*, but the
difference between old and new results cannot be attributed.

## 6. ADT vs. RSD — OPEN

Standing plan is ADT primary, RSD sensitivity (`docs/detector_comparison_adt_rsd.md`).
Not final. Decide after validating both against the Empatica per-minute
`pulse-rate` biomarker, which has never been done for either detector.

Sub-decision: whether to fix the ADT index-0 fabricated interval
(`docs/adt_audit.md`) in the primary pipeline. Fixing it is correct; it also means
the primary pipeline is no longer literally identical to the original detector.
Either choice is defensible and must be stated explicitly in the methods.

## 7. Quality-gate thresholds — OPEN

The previous pipeline used `min 5 valid IBIs`, `coverage >= 0.50`,
`motion <= 0.050 g`, `wear >= 50%`. These were set for a different study,
different participants, and a different peak detector. For SAR they need to be
re-justified or re-tuned, and the results reported at more than one setting.

Additionally: are per-participant tuned detector parameters acceptable in this
study, or must one parameter set apply to everyone? The previous pipeline tuned
`prominence` and `rel_threshold` per participant.

## 8. Baseline definition — NEEDED

What counts as baseline for SAR? The previous study had an explicit multi-day
free-living baseline segment between visits. The SAR design is not documented in
the audited code — the baseline notebooks simply pool every RMSSD row from every
date. Unresolved: whether baseline means a designated pre-robot period, all
non-robot time, or a separate recording, and whether sleep is included.

## 9. Spike direction — NEEDED

Swetha's stage 4 flags only downward deviations (`RMSSD < mean − N·SD`) while
computing nothing for the upward side. The previous pipeline flags both. Which
does the manuscript claim, and is the upward direction reported anywhere?

## 10. Effect of the windowing correction on the manuscript — NEEDED

Correcting rolling-per-beat to non-overlapping 60 s changes the baseline SD, and
therefore every spike threshold and every spike count
(`docs/rmssd_windowing_audit.md`). How this is presented — corrected results
throughout, or old and new side by side — is a manuscript decision to be made
before the numbers are regenerated, not after.

## 11. EMA codebook — NEEDED

`ema_interaction` needs a fixed vocabulary. The EMA item wording, response
options, and how a response maps onto a 60 s window (nearest window? the window
containing the response? a window of interest preceding it?) are not established.
The temporal alignment rule in particular is an analysis decision, not an
implementation detail.

## 12. Clemson device and firmware parity — NEEDED

Whether Clemson used the same Empatica EmbracePlus generation and firmware as
DePaul, and whether the Clemson downloads include the
`digital_biomarkers/aggregated_per_minute/*` files (wearing detection, accel SD,
pulse rate). If they do not, `wear_percentage`, `motion_metric` and the detector
validation are unavailable for that site, and the quality gate cannot be applied
symmetrically across sites.
