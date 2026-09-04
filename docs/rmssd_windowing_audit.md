# RMSSD windowing: manuscript vs. Swetha implementation

Created: 2026-09-03
Last updated: 2026-09-03

**Claim under test.** The manuscript states RMSSD is computed over 60-second
**non-overlapping** windows.

**Code as written** (`Swetha 2_HRV_RMSSDfor30mins (1).ipynb`, function
`get_time_domain_HRV`, defined inline inside the per-date processing loop):

```python
df["dt"] = pd.to_datetime(df["ts"], unit="s")
roll_args = {"min_periods": 1, "center": center}       # center=True by default
if use_time:
    roll_args.update({"on": "dt", "window": f"{window_length}s"})   # "60s"

df["RMSSD"] = df["diff"] ** 2
df["RMSSD"] = np.sqrt(df.rolling(**roll_args)["RMSSD"].mean())
```

Called as `get_time_domain_HRV(IBI_df, window_length=60, use_time=True)`.

`IBI_df` has **one row per detected beat**. `pandas.rolling` returns one output
value per input row. Therefore the operation is a per-beat sliding window, not a
partition of the timeline.

## Findings

**1. Rolling, not non-overlapping.** Confirmed. `DataFrame.rolling(window="60s")`
is a sliding window evaluated at every row. There is no `resample`, no
`pd.Grouper`, and no floor-to-minute anywhere in the notebook. With `center=True`
each window spans roughly ±30 s around its own beat.

**2. Observations per minute.** One per beat, i.e. equal to the instantaneous
heart rate in BPM. Measured on a synthetic 72 BPM, ~5 minute IBI series through
the exact expression above:

```
n beats                360
n RMSSD rows           360
duration               298.7 s
RMSSD rows per minute  72.3
true non-overlapping 60 s windows over the same span   5
```

So the implementation produces on the order of **60–100 RMSSD values per minute**
where the manuscript describes **1**. For the SAR participants that is roughly a
70-fold inflation of the apparent sample size.

**3. Adjacent estimates share underlying IBIs.** Yes — almost completely. Two
consecutive rows are separated by one beat (~0.83 s) while each window spans 60 s,
so they share ~59/60 of their IBIs. Measured lag-1 autocorrelation of the RMSSD
series in the same synthetic run: **0.990**. Consecutive rows are not independent
observations in any statistical sense.

**4. Does the implementation differ from the manuscript?** Yes, materially, and
in ways that propagate:

- **Baseline SD is wrong.** The baseline mean is roughly unbiased (it is a
  heart-rate-weighted average of overlapping estimates rather than a plain
  average, a minor bias), but the SD of an autocorrelated smoothed series is far
  smaller than the SD of independent 60 s windows. Since the spike rule is
  `RMSSD < mean − N·SD`, an understated SD makes the threshold **less extreme**
  and flags more windows than the stated method would.
- **Spike duration is in beats.** `Spike_Duration` counts flagged rows. A
  one-minute spike reports ~72.
- **Minute-level counts are not minutes.** Any "number of spike minutes" derived
  from these rows is a beat count.
- **Any test treating rows as independent is invalid** at this resolution — the
  effective sample size is ~1/70 of the row count.
- **Heart-rate weighting.** Because rows are emitted per beat, participants and
  periods with higher HR contribute proportionally more rows to the baseline.
  Tachycardic (i.e. stressed) periods are over-weighted in the very baseline the
  stress spikes are measured against.

Additionally, `min_periods=1` means a window holding a single successive
difference returns `RMSSD = |that difference|` rather than `NaN`, so sparse or
poorly detected stretches emit values that look like data.

## Recommendation

Compute RMSSD on a true non-overlapping 60 s UTC grid: one row per interval,
`n_total_ibi` / `n_valid_ibi` / `coverage` on every row, `rmssd_ms = NaN` when the
minimum beat and coverage requirements are not met. The beat-level rolling series
can be kept as a diagnostic artifact for plotting, clearly named
(`rmssd_rolling_beatlevel.csv`) and never used for statistics.

Because this changes the baseline SD, **every spike count in the original analysis
will change**. That is a manuscript-level correction, not a refactor.
