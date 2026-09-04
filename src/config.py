"""Configuration loading and validation.

Created: 2026-09-03
Last updated: 2026-09-03

Three files describe a run:

* ``config/pipeline.yaml``           — every analysis parameter
* ``config/sites.yaml``              — site -> timezone (the only timezone literals)
* ``config/participants.csv``        — the participant registry, committed, IDs only
* ``config/participants.local.csv``  — gitignored, maps an ID to its real data path

The registry is split because this repository shares a directory with the raw
data, whose participant folders are named with real first names. The committed
file must never carry one, and ``load_participants`` enforces that rather than
trusting anyone to remember it.

Nothing in this package reads a participant ID, a path, a date range, or a
timezone from anywhere else. Loading validates rather than repairing: a malformed
row raises, because a silently skipped participant is a result that looks complete
and is not.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import pandas as pd
import yaml

CONFIG_DIR = Path(__file__).resolve().parent.parent / "config"

PARTICIPANT_COLUMNS = [
    "participant_id",
    "site",
    "wearable_folder",
    "ema_id",
    "timezone",
    "robot_delivery",
    "analysis_include",
    "exclusion_reason",
]


class ConfigError(ValueError):
    """Raised when a config file is malformed. Never downgraded to a warning."""


@dataclass(frozen=True)
class RunConfig:
    """One run's full parameter set, plus a hash of it for the run manifest."""

    pipeline: dict
    sites: dict
    participants: pd.DataFrame
    config_hash: str


def _load_yaml(path: Path) -> dict:
    with open(path) as fh:
        return yaml.safe_load(fh)


def load_sites(path: Path | None = None) -> dict:
    """Site metadata keyed by site code. Validates that every timezone resolves."""
    data = _load_yaml(path or CONFIG_DIR / "sites.yaml")["sites"]
    for site, meta in data.items():
        tz = meta.get("timezone")
        if not tz:
            raise ConfigError(f"site {site!r} has no timezone")
        try:
            ZoneInfo(tz)
        except ZoneInfoNotFoundError as exc:
            raise ConfigError(f"site {site!r} has unknown timezone {tz!r}") from exc
    return data


def load_participants(path: Path | None = None, sites: dict | None = None,
                      local_path: Path | None = None,
                      allow_paths: bool = False) -> pd.DataFrame:
    """Read and validate ``config/participants.csv``.

    Blank cells stay blank (``pd.NA``); no value is defaulted or inferred. The
    template ships with zero rows, which is a valid — and currently correct —
    state: the participant mappings are unresolved (docs/open_questions.md).
    """
    path = path or CONFIG_DIR / "participants.csv"
    local_path = local_path or CONFIG_DIR / "participants.local.csv"
    sites = sites if sites is not None else load_sites()

    df = pd.read_csv(path, dtype=str, keep_default_na=True)

    missing = [c for c in PARTICIPANT_COLUMNS if c not in df.columns]
    if missing:
        raise ConfigError(f"participants.csv missing columns: {missing}")

    if df.empty:
        return df[PARTICIPANT_COLUMNS]

    dupes = df.loc[df["participant_id"].duplicated(), "participant_id"].tolist()
    if dupes:
        raise ConfigError(f"duplicate participant_id: {dupes}")

    unknown = sorted(set(df["site"].dropna()) - set(sites))
    if unknown:
        raise ConfigError(f"unknown site(s): {unknown}; known: {sorted(sites)}")

    # Per-participant timezone override is optional, but must be real if present.
    for tz in df["timezone"].dropna().unique():
        try:
            ZoneInfo(tz)
        except ZoneInfoNotFoundError as exc:
            raise ConfigError(f"unknown timezone override {tz!r}") from exc

    # The committed registry must not carry data paths: the real folder names
    # contain participant first names, so a filled-in wearable_folder here is the
    # one edit that would put a name in a public commit. Paths come from the
    # gitignored local file instead.
    if not allow_paths:
        leaked = df.loc[df["wearable_folder"].fillna("").str.strip() != "",
                        "participant_id"].tolist()
        if leaked:
            raise ConfigError(
                "wearable_folder must be blank in the committed participants.csv "
                f"(offending rows: {leaked}); put paths in participants.local.csv, "
                "or set allow_paths_in_committed_config: true in pipeline.yaml"
            )

    include = df["analysis_include"].str.strip().str.lower()
    bad = df.loc[~include.isin({"true", "false"}), "participant_id"].tolist()
    if bad:
        raise ConfigError(f"analysis_include must be true/false for: {bad}")

    # An exclusion without a stated reason is how participants quietly vanish.
    excluded_no_reason = df.loc[
        (include == "false") & (df["exclusion_reason"].fillna("").str.strip() == ""),
        "participant_id",
    ].tolist()
    if excluded_no_reason:
        raise ConfigError(f"excluded participants need exclusion_reason: {excluded_no_reason}")

    df["analysis_include"] = include == "true"
    df = _merge_local_paths(df, local_path)
    return df[PARTICIPANT_COLUMNS]


def _merge_local_paths(df: pd.DataFrame, local_path: Path) -> pd.DataFrame:
    """Fill ``wearable_folder`` from the gitignored local mapping, if present.

    A missing local file is not an error — the registry is still valid, the
    participants simply have no resolvable data path on this machine, and the
    stage that needs one reports it rather than guessing a folder.
    """
    if not Path(local_path).exists():
        return df

    local = pd.read_csv(local_path, dtype=str, keep_default_na=True)
    required = {"participant_id", "wearable_folder"}
    missing = required - set(local.columns)
    if missing:
        raise ConfigError(f"{local_path.name} missing columns: {sorted(missing)}")
    if local.empty:
        return df

    dupes = local.loc[local["participant_id"].duplicated(), "participant_id"].tolist()
    if dupes:
        raise ConfigError(f"duplicate participant_id in {local_path.name}: {dupes}")

    # A local row for someone not in the registry means the two files disagree
    # about who is in the study, which is exactly the kind of drift that silently
    # attaches one participant's data to another's ID.
    unknown = sorted(set(local["participant_id"]) - set(df["participant_id"]))
    if unknown:
        raise ConfigError(
            f"{local_path.name} names participants absent from participants.csv: {unknown}"
        )

    mapping = dict(zip(local["participant_id"], local["wearable_folder"]))
    df = df.copy()
    df["wearable_folder"] = df["participant_id"].map(mapping).fillna(df["wearable_folder"])
    return df


def participant_timezone(row: pd.Series, sites: dict) -> str:
    """IANA timezone for one participant: explicit override, else the site's."""
    tz = row.get("timezone")
    if isinstance(tz, str) and tz.strip():
        return tz.strip()
    return sites[row["site"]]["timezone"]


def load_run_config(config_dir: Path | None = None) -> RunConfig:
    """Load all three config files and hash them for the run manifest."""
    config_dir = config_dir or CONFIG_DIR
    pipeline_path = config_dir / "pipeline.yaml"
    sites_path = config_dir / "sites.yaml"
    participants_path = config_dir / "participants.csv"

    sites = load_sites(sites_path)
    pipeline = _load_yaml(pipeline_path)
    participants = load_participants(
        participants_path, sites,
        local_path=config_dir / "participants.local.csv",
        allow_paths=bool(pipeline.get("allow_paths_in_committed_config", False)),
    )

    # Hash the raw bytes of all three files: two runs with the same hash and the
    # same inputs must produce identical outputs (docs/idempotency.md).
    digest = hashlib.sha256()
    # participants.local.csv is deliberately excluded: it is machine-specific and
    # holds only path mappings, so hashing it would make two machines analysing
    # the same data report different config hashes.
    for p in (pipeline_path, sites_path, participants_path):
        digest.update(p.read_bytes())

    return RunConfig(pipeline=pipeline, sites=sites, participants=participants,
                     config_hash=digest.hexdigest()[:16])
