# ADT audit — `Swetha ADT (2).py`

Created: 2026-09-03
Last updated: 2026-09-03

Adaptive-threshold systolic peak detector, implementation of the Shin et al.
adaptive-thresholding method. Read-only audit; the file was not modified.

## Algorithm parameters

| Constant | Value | Role |
|---|---|---|
| `MIN_INTERVAL` | 0.350 s | Lower bound for an IBI to be counted as "valid" for the refractory estimate (171 BPM). Comment says "set arbitrarily". |
| `MAX_INTERVAL` | 1.200 s | Upper bound for the same (50 BPM). |
| `NUM_PREVIOUS` | 6 | Number of recent valid IBIs averaged to predict the next beat interval. |
| `REFRACTORY_PERIOD_PERCENTAGE` | 0.6 | Refractory period = 0.6 × mean of the last 6 valid IBIs. |
| `MAX_SLOPE_CHANGING_RATE` | −1.2 | Multiplier in the slope-parameter update. |
| `WINDOW_SECONDS` | 3 | Trailing window for the running signal SD used in the slope update. |
| `fixed_slope_parameter` | 0.6 (constructor default) | Used **only** to seed the initial slope; overwritten after the first detection. |

Note these are in-algorithm gates only. They do **not** filter the returned
peaks: `ADT_peaks` returns every `fiducial_points` entry regardless of whether the
interval that produced it was inside `[MIN_INTERVAL, MAX_INTERVAL]`.

## Physiological IBI limits

`MIN_INTERVAL`/`MAX_INTERVAL` (0.350–1.200 s) gate only `valid_IBIs`, the buffer
used to size the refractory period. The effective floor on the *output* peak
spacing is the refractory period itself, `0.6 × mean(last 6 valid IBIs)` — at a
typical 0.83 s mean that is ~0.50 s (120 BPM), and if the buffer degrades toward
`MIN_INTERVAL` it can fall to ~0.21 s (285 BPM). There is no output-side ceiling
at all: a missed beat yields an IBI of ~1.7 s and the detector emits it.

Downstream, `2_HRV_RMSSDfor30mins` applies only `IBI > 1.15 s → NaN`. Nothing
rejects short IBIs. The combination means split-beat detections in the
0.35–0.50 s range survive into RMSSD.

## Refractory-period logic

On each detection (`fiducial_point_located`):
1. Append the index to `fiducial_points`.
2. Set `threshold[-1] = signal[index]` (threshold jumps to the peak amplitude).
3. `adjust_slope_parameter`: `slope = −1.2 × (signal[last_fiducial] + rolling_std[index]) / fs`.
4. `calculate_refractory_period`: new IBI from the last two fiducial times; if in
   (0.350, 1.200] append it to `valid_IBIs`; refractory = `mean(valid_IBIs[-6:]) × 0.6`.
5. Extend `threshold` by `int(refractory × fs)` samples of linear decay
   `threshold[-1] + k·slope`, and return that count so the main loop skips
   forward past the refractory period.

The threshold list stays the same length as the number of samples consumed, so
`threshold[-1]` remains the current threshold. That bookkeeping is correct.

**Risk in the slope update.** `signal` here is the *rolling-standardised* PPG, so
`signal[last_fiducial]` is in SD units and can in principle be negative. If
`signal[last_fiducial] + rolling_std[index] < 0`, the slope becomes **positive**
and the threshold *rises* during the refractory period instead of decaying. The
threshold then only ever decreases via Case 1 (`threshold += slope`, also
positive), so it can run away upward and suppress all subsequent detections for
the remainder of the record. In practice systolic peaks sit at ~2–3 SD so this is
unlikely on clean data, but it is unguarded and there is no diagnostic for it.
Any long stretch of zero detected beats in the SAR outputs should be checked
against this.

## Initialization behavior

```python
self.threshold       = [0.2 * np.median(signal)]
self.max_slope_parameter = -abs(0.6 * self.threshold[-1])
self.fiducial_points = [0]
self.valid_IBIs      = [0.650]
```

- On a rolling-standardised signal `np.median(signal) ≈ 0`, so the initial
  threshold is ≈ 0 and the initial slope ≈ 0. The first sample above zero that is
  a local maximum is therefore detected as a beat, whatever it is.
- `valid_IBIs = [0.650]` is a seed value so `np.mean` has something to average.
  It stays in the buffer and biases the first several refractory periods until
  six real IBIs push it out.

## Does fiducial point index 0 create a false beat?

**Yes — one fabricated interval per processed file.**

`fiducial_points` is initialised to `[0]`, and index 0 is not a detected beat; it
is the first sample of the record. Consequences:

1. **Inside the algorithm.** The first real detection computes
   `new_IBI = ts[first_peak] − ts[0]`. That is the time from the start of the
   recording to the first beat — an arbitrary offset, not a heart interval. If it
   happens to land in (0.350, 1.200] it is appended to `valid_IBIs` and biases
   the first six refractory periods. If the record starts mid-beat, it does not,
   and the seed 0.650 governs instead.
2. **In the returned array.** `ADT_peaks` returns `np.array(detector.fiducial_points)`
   with the 0 still in it. In the notebook, `detect_abnormal_beats` builds
   `IBI = result_df["ts"].diff()`, so row 0 gets `NaN` (harmless) but **row 1 gets
   `ts[first_real_peak] − ts[0]`**, a spurious IBI presented as real.
3. **Propagation.** That spurious IBI also enters `diff = IBI.diff()*1e3`, so it
   corrupts the first *two* successive differences. Under the `min_periods=1`
   rolling window it can dominate RMSSD for the first ~30 s of every file. With
   ~30-minute AVRO-derived files processed per date, this is one corrupted
   interval and up to a minute of contaminated RMSSD **per file**, systematically
   at file starts.

Fix is one line at the boundary — drop index 0 from the returned peaks, or start
`fiducial_points` empty and special-case the first detection. **Not applied.** The
detector is unchanged pending the ADT-vs-RSD decision.

## Other edge cases

- `check_inflection(index, smooth=1)` takes `np.mean` of `signal[max(0,i-1):i]`
  and `signal[i+1:min(n,i+2)]`. At `i = 0` the "before" slice is empty and at
  `i = n−1` the "after" slice is empty; `np.mean([])` returns `nan` with a
  `RuntimeWarning`, and every comparison against `nan` is `False`, so no detection
  fires at the array edges. Behaviourally acceptable, noisy in the logs.
- The `smooth=1` default means the inflection test compares a point to exactly one
  neighbour on each side. The docstring says "the mean of the 5 before it and
  after it". Code and comment disagree; the code is a 3-point test.
- `signal_STD` uses `min_periods=1` then `.bfill()`. With `min_periods=1` the
  first value is the SD of a single sample, which is `NaN`, so `bfill` is doing
  real work at the start of every record.
- `self.ts` is indexed positionally (`self.ts[self.fiducial_points[-1]]`). The
  notebook passes `df["ts"]`, a Series. It works only because the DataFrame is
  rebuilt with a fresh `RangeIndex` after interpolation. Passing a sliced Series
  with a non-zero-based index would silently produce wrong IBIs or `KeyError`.
- Peaks are systolic peaks, so IBIs are peak-to-peak. RSD uses onset-to-onset.
  The two are not interchangeable without re-deriving intervals.
- No handling for `len(signal) == 0` or all-NaN input.

## Validation status against Empatica pulse-rate data

**No validation found anywhere.** Searched the Swetha notebooks and `ADT.py`: the
Empatica `pulse-rate` and `prv` per-minute digital biomarkers are never read.
Notebook 1 converts `accelerometer, gyroscope, temperature, eda, steps, bvp` from
the AVROs and the `digital_biomarkers/aggregated_per_minute/*` files are not
touched by any stage. There is no comparison of ADT-derived HR against Empatica's
own pulse rate, no Bland–Altman, no beat-detection accuracy figure, and no
reference-annotated segment.

This is the single largest unverified assumption in the original pipeline, and it
is cheap to close: Empatica ships `*_pulse-rate.csv` and `*_prv.csv` per minute in
every download. Recommended first validation task once the SAR raw data is
located — compare per-minute mean HR from ADT beats against Empatica pulse rate
for every participant, and repeat for RSD. That comparison is also the natural
tie-breaker for the ADT-vs-RSD decision.
