"""Stage 1 — Empatica AVRO -> per-participant sensor tables.

Created: 2026-09-03
Last updated: 2026-09-03

Design (contrast with both source pipelines in docs/pipeline_comparison.md):

* Files are discovered recursively under the participant's ``wearable_folder``
  from config/participants.csv and ordered by the UNIX-second integer embedded in
  the filename. No hard-coded date lists, no absolute paths, no participant name
  anywhere.
* ``timestampStart`` is UNIX microseconds, already UTC. Stored as int64; converted
  to tz-aware UTC on load. No local-time string column is written next to raw
  samples — that is what rendered Clemson data in Chicago time.
* Writing is streamed with boundary de-duplication (drop any sample whose
  timestamp is <= the last written for that sensor) and the output file is
  replaced, never appended to. Re-running is a no-op on the result.
* The per-minute ``digital_biomarkers/aggregated_per_minute/*`` files are read
  too: wearing detection, accelerometer SD, and pulse rate. The original pipeline
  converted the accelerometer and then never used it, and never touched pulse
  rate — which is why no beat detector in this project has ever been validated.

Raw data is read-only. Nothing here sorts, rewrites, or de-duplicates a source
file in place.
"""

from __future__ import annotations

import pandas as pd

SENSORS = ["bvp", "accelerometer", "temperature", "eda", "steps"]
BIOMARKERS = ["wearing-detection", "accelerometers-std", "pulse-rate", "prv"]


def find_avro_files(wearable_folder, raw_root) -> list:
    """All AVRO paths for one participant, ordered by embedded start time."""
    raise NotImplementedError("stage 1 not implemented — audit/architecture phase")


def convert_participant(participant_id: str, wearable_folder, raw_root, out_root) -> dict:
    """Convert one participant's AVROs to per-sensor tables. Returns row counts."""
    raise NotImplementedError("stage 1 not implemented — audit/architecture phase")


def load_biomarker(participant_id: str, name: str, raw_root) -> pd.DataFrame:
    """One per-minute Empatica biomarker as ``ts_utc`` + its value column.

    Used for ``wear_percentage`` (wearing-detection), ``motion_metric``
    (accelerometers-std), and detector validation (pulse-rate).
    """
    raise NotImplementedError("stage 1 not implemented — audit/architecture phase")
