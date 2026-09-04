"""Deterministic, idempotent table writing.

Created: 2026-09-03
Last updated: 2026-09-03

Policy in docs/idempotency.md. Running a stage twice over identical inputs must
produce byte-identical outputs, so every write goes through here: fixed column
order, fixed sort, uniqueness check, atomic replace. Nothing appends.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

import pandas as pd

FLOAT_FORMAT = "%.6f"      # fixed so two runs format floats identically


class DuplicateRowsError(ValueError):
    """A table violated its uniqueness key."""


def assert_unique(df: pd.DataFrame, keys: list[str], name: str) -> None:
    """Raise if ``keys`` are not unique in ``df``.

    Duplicates are an error, not something to de-duplicate quietly: two rows with
    the same key mean two computations disagreed, and that needs to be looked at.
    """
    missing = [k for k in keys if k not in df.columns]
    if missing:
        raise DuplicateRowsError(f"{name}: key columns absent: {missing}")
    dup = df.duplicated(subset=keys, keep=False)
    if dup.any():
        offenders = df.loc[dup, keys].drop_duplicates().head(10).to_dict("records")
        raise DuplicateRowsError(
            f"{name}: {int(dup.sum())} rows violate uniqueness on {keys}; "
            f"first offenders: {offenders}"
        )


def write_table(df: pd.DataFrame, path: str | Path, *, keys: list[str],
                sort_by: list[str] | None = None,
                columns: list[str] | None = None) -> Path:
    """Sort, reorder, check uniqueness, then write atomically.

    Atomic means: write ``path.tmp`` in the same directory and ``os.replace`` it
    into place. A crashed run leaves the previous complete file or nothing, never
    a truncated file that the next stage reads as if it were whole.
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    out = df.copy()
    if columns is not None:
        missing = [c for c in columns if c not in out.columns]
        if missing:
            raise ValueError(f"{path.name}: missing expected columns {missing}")
        out = out[columns]
    out = out.sort_values(sort_by or keys, kind="mergesort").reset_index(drop=True)
    assert_unique(out, keys, path.name)

    tmp = path.with_suffix(path.suffix + ".tmp")
    out.to_csv(tmp, index=False, float_format=FLOAT_FORMAT)
    os.replace(tmp, path)
    return path


def upsert_participant_rows(df: pd.DataFrame, path: str | Path, participant_id: str,
                            *, keys: list[str], sort_by: list[str] | None = None,
                            columns: list[str] | None = None) -> Path:
    """Replace one participant's rows in an existing table, then rewrite it whole.

    This is a replace-by-key, not an append: the participant's existing rows are
    dropped before the new ones go in, so re-running a single participant can
    never duplicate them.
    """
    path = Path(path)
    if path.exists():
        existing = pd.read_csv(path)
        existing = existing[existing["participant_id"] != participant_id]
        combined = pd.concat([existing, df], ignore_index=True)
    else:
        combined = df
    return write_table(combined, path, keys=keys, sort_by=sort_by, columns=columns)


def write_manifest(run_id: str, *, results_root: str | Path, config_hash: str,
                   code_revision: str, inputs: list[str | Path],
                   outputs: dict[str, int], extra: dict | None = None) -> Path:
    """Record what produced a set of outputs, for reproduction and comparison.

    Two runs whose manifests agree on ``config_hash`` and the input list must
    produce identical outputs; if they do not, the manifests localise the change.
    """
    manifest_dir = Path(results_root) / "manifests"
    manifest_dir.mkdir(parents=True, exist_ok=True)

    input_records = []
    for p in inputs:
        p = Path(p)
        stat = p.stat() if p.exists() else None
        input_records.append({
            "path": str(p),
            "bytes": stat.st_size if stat else None,
            "mtime_unix": int(stat.st_mtime) if stat else None,
        })

    payload = {
        "run_id": run_id,
        "utc_written": pd.Timestamp.utcnow().isoformat(),
        "config_hash": config_hash,
        "code_revision": code_revision,
        "inputs": input_records,
        "output_row_counts": outputs,
        **(extra or {}),
    }
    path = manifest_dir / f"{run_id}.json"
    tmp = path.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(payload, indent=2, sort_keys=True))
    os.replace(tmp, path)
    return path
