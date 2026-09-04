# Peak detectors: ADT vs. RSD

Created: 2026-09-03
Last updated: 2026-09-03

RSD source: `~/Documents/empatica-hrv-pipeline/utils/rsd.py`, implementing the
method in Andrew Murphy's DePaul thesis (2025), "Evaluating wrist placement and
signal processing techniques for real-world HRV monitoring using PPG".
ADT source: `~/Downloads/Swetha ADT (2).py` (audited in `docs/adt_audit.md`).

## RSD, as implemented

1. Split the series wherever inter-sample spacing exceeds `5/fs` (watch-off and
   file-boundary gaps), so no interpolation crosses a gap.
2. Cubic-spline upsample 64 → 240 Hz per contiguous run.
3. Butterworth bandpass 0.4–8 Hz, order 4, zero-phase.
4. First and second derivatives (VPG, APG) by finite difference.
5. Rolling-standardise PPG, VPG and APG independently over 0.650 s, centered.
6. Composite = mean(standardised PPG, −standardised APG).
7. For each prominent composite maximum, walk back to the nearest prominent
   composite minimum and require a full ordered five-point sequence
   `onset ≤ a-peak ≤ u-peak ≤ b-trough < systolic`, with the u-peak strictly
   interior. `u-peak` = max VPG; `a-peak` = max APG before it; `b-trough` = min
   APG after it. Beats failing the ordering are discarded.
8. **IBIs between successive onsets**, timestamped at the closing onset.
9. Long segments run through `run_rsd_chunked`: 180 s chunks with 5 s overlap,
   onsets kept only from each chunk's core.

## Differences

| Axis | ADT | RSD |
|---|---|---|
| Fiducial used for the interval | Systolic peak | Pulse onset |
| Decision rule | Sequential threshold that decays over time and is reset by each detection | Prominence-based extrema on a composite signal, then a morphological validity check |
| Memory | Yes — threshold, slope and a 6-IBI buffer carry forward through the record | No — `find_peaks` is stateless over the whole run; only chunk boundaries matter |
| Failure mode | Threshold drift; can under-detect for long stretches after a bad update (see the positive-slope risk in `docs/adt_audit.md`) | Prominence mis-set: too low double-detects the dicrotic notch, too high drops beats. Fails locally, not persistently |
| Rejection of implausible beats | Refractory period only; no output-side bounds | Five-point ordering test plus `min_ibi_s`/`max_ibi_s` spacing constraints |
| Gap handling | None in the detector; whatever the caller passes | Explicit gap splitting before interpolation |
| Tunable surface | 6 class constants, none exposed as arguments | `prominence`, `min_ibi_s`, `max_ibi_s` as arguments; tuned per participant in the previous study |
| Determinism | Deterministic; sequential, so a single early difference can change all later detections | Deterministic; local, so a perturbation stays local |
| Cost | Single pass, cheap | Upsample + filter + two derivatives + three rolling standardisations; noticeably heavier |
| Provenance in this project | Used for every number in the original SAR analysis | Used for the previous DePaul HRV study, never on SAR data |
| Known defect | Index-0 initialisation fabricates one interval per file | Parameters were tuned on 5 DePaul participants and are not established as transferable |

## Standing plan (not final)

- **Primary = ADT.** Keeps the corrected pipeline's peak detection identical to
  the original study, so that every change in the results is attributable to the
  windowing, quality-control and baseline corrections rather than to a different
  beat detector.
- **Sensitivity = RSD.** Re-run end to end; report whether the direction and
  significance of the conclusions survive a change of detector.

Preconditions before that becomes final, in order:
1. Validate both detectors against the Empatica per-minute `pulse-rate` biomarker
   for every participant (`docs/adt_audit.md` — no such validation exists yet).
2. Decide whether the ADT index-0 fabricated interval is fixed in the primary
   pipeline. Fixing it is correct but makes "identical to the original" no longer
   literally true; it should be stated as a documented correction either way.
3. Confirm ADT's behaviour on Clemson data, which may come from different device
   firmware than DePaul's.

Both detectors sit behind one interface so the choice is a config value:

```yaml
peak_detector: adt        # adt | rsd
```
