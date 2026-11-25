"""Board size and the line-clear score table.

The search reward is separate from this table. A four-line clear scores 800
here, while the heuristic counts it as four lines.
"""

from __future__ import annotations

COLS = 10
ROWS = 20
EMPTY = 0

# 100, 300, 500, 800 for one through four lines.
LINE_SCORES = {1: 100, 2: 300, 3: 500, 4: 800}

# Benchmark cap. A hard drop has no clock, so pieces placed is survival.
MAX_PIECES = 10_000


def line_score(cleared: int) -> int:
    """Points awarded for clearing `cleared` lines with one lock."""
    return LINE_SCORES.get(cleared, 0)
