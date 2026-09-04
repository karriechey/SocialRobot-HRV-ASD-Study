# Timezone policy

Created: 2026-09-03
Last updated: 2026-09-03

## Rules

1. **UTC is canonical.** Every timestamp stored in any processed artifact is
   timezone-aware UTC. Window boundaries, IBI onsets, EMA response times, phase
   boundaries — all UTC.
2. **No naive timestamps after parsing.** A value is localised at the moment it is
   read and is tz-aware from then on. A naive timestamp reaching any function
   downstream of ingestion is a bug and raises.
3. **Local time is a display projection.** Computed at report time from the
   participant's site timezone, written to `*_local` columns for human reading,
   never used for joins, comparisons, arithmetic, or filtering.
4. **Site drives the timezone**, from `config/participants.csv`:

   | Site | IANA timezone |
   |---|---|
   | DePaul | `America/Chicago` |
   | Clemson | `America/New_York` |

   No timezone literal appears in any module. The mapping lives in
   `config/sites.yaml` and is looked up per participant.
5. **DST is handled by the tz database**, via `zoneinfo` / `pandas.tz_localize`.
   No fixed UTC offsets, no `utcfromtimestamp`, no manual hour arithmetic. Both
   sites observe DST and the SAR collection windows cross transitions.

## AVRO / wearable timestamps

Empatica `timestampStart` is UNIX **microseconds since epoch, already UTC**. It is
converted with `pd.to_datetime(us, unit="us", utc=True)`. No localisation step is
involved and no site information is needed. The previous pipeline's practice of
writing an `America/Chicago` string column next to raw samples is dropped —
it is redundant with the UTC value and was the mechanism by which Clemson data
was rendered in the wrong local time.

## EMA timestamps

EMA exports carry **naive local wall-clock** values. They are handled as:

```python
local = pd.to_datetime(raw_value)                  # naive
aware = local.tz_localize(site_tz,                 # site from participants.csv
                          nonexistent="raise",
                          ambiguous="raise")
utc   = aware.tz_convert("UTC")
```

`nonexistent="raise"` and `ambiguous="raise"` are deliberate. A naive local time
inside the spring-forward gap does not exist, and a time inside the fall-back hour
is ambiguous; both indicate a data problem that must be resolved by hand and
recorded, not silently shifted or assumed. Any raise is logged with the
participant, the raw value, and the site, and the affected row is quarantined
rather than dropped.

## Two-site correctness check

The regression that motivates all of the above: the original pipeline hard-coded
`America/Chicago` in every conversion, including the loop over the Clemson data
folder. Every Clemson local timestamp was one hour off, which is the resolution
at which EMA responses are matched to HRV minutes.

A unit test asserts that a fixed UTC instant renders to different local wall-clock
times for a DePaul and a Clemson participant, and that both round-trip back to the
same UTC instant.
