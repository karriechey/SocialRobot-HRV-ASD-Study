"""EMA responses: naive local timestamps -> UTC, then aligned to windows.

Created: 2026-09-03
Last updated: 2026-09-03

EMA exports carry naive local wall-clock times. Each is localised with the
participant's **site** timezone before conversion to UTC
(``src.timezones.localize_naive_local``), with DST gaps and ambiguous hours raised
rather than guessed. The original pipeline hard-coded ``America/Chicago`` for both
sites, so every Clemson local time was an hour off — at the resolution EMA
responses are matched to HRV minutes.

Participants are joined on ``ema_id`` from config/participants.csv, which is not
the same as ``participant_id``.

Two things are deliberately unimplemented because they are analysis decisions, not
implementation details (docs/open_questions.md item 11): the ``ema_interaction``
vocabulary, and the rule mapping a response instant onto a 60 s window (the window
containing the response? the nearest? a fixed window preceding it?).
"""

from __future__ import annotations

import pandas as pd


def load_ema(path, participants: pd.DataFrame, sites: dict) -> pd.DataFrame:
    """Read an EMA export, localise per site, return UTC-stamped responses."""
    raise NotImplementedError("not implemented — awaiting the EMA codebook")


def align_to_windows(windows: pd.DataFrame, ema: pd.DataFrame, rule: str) -> pd.DataFrame:
    """Attach ``ema_interaction`` and ``ema_response_timestamp`` to windows."""
    raise NotImplementedError("not implemented — alignment rule undecided")


def assign_phase(windows: pd.DataFrame, participants: pd.DataFrame) -> pd.DataFrame:
    """Label each window ``pre_robot`` / ``robot`` / ``post_robot`` / ``baseline``.

    Windows for a participant whose ``robot_delivery`` boundaries are blank are
    labelled ``unassigned``. The boundaries are not inferred from EMA timing or
    from the shape of the data (docs/open_questions.md item 3).
    """
    raise NotImplementedError("not implemented — robot delivery boundaries unknown")
