"""Board features for the one-ply evaluation.

H(s) = 1.0*L - 0.5*A - 0.7*holes - 0.3*B

L is supplied by the simulator, because the cleared rows are gone before A,
holes, and B are measured. The integer rank is 10*H, so these weights compare
exactly. They were not fit by a search.

Per unit, holes are the strongest penalty, then height, then roughness.
"""

from __future__ import annotations

from game.board import Board
from game.constants import COLS, EMPTY, ROWS

W_LINES = 1.0
W_HEIGHT = 0.5
W_HOLES = 0.7
W_BUMP = 0.3

FORMULA = "H(s) = 1.0*L - 0.5*A - 0.7*holes - 0.3*B"


def measure(board: Board) -> tuple[int, int, int]:
    """Return aggregate height, holes, and bumpiness of a locked board.

    Column height is the distance from the bottom of the well to the highest
    block, so a hole still counts toward height. A hole is an empty cell with
    a block above it in the same column. Bumpiness is the sum of absolute
    height gaps between neighboring columns.
    """
    heights = [0] * COLS
    holes = 0
    for col in range(COLS):
        seen = False
        for row in range(ROWS):
            if board[row][col] != EMPTY:
                if not seen:
                    heights[col] = ROWS - row
                    seen = True
            elif seen:
                holes += 1
    aggregate = sum(heights)
    bumpiness = sum(abs(heights[col] - heights[col + 1]) for col in range(COLS - 1))
    return aggregate, holes, bumpiness


def published_h(lines: int, aggregate: int, holes: int, bumpiness: int) -> float:
    """The weighted sum in the published scale."""
    return (
        W_LINES * lines
        - W_HEIGHT * aggregate
        - W_HOLES * holes
        - W_BUMP * bumpiness
    )


def heuristic_value(lines: int, aggregate: int, holes: int, bumpiness: int) -> int:
    """10*H, in integers, used to rank drops."""
    return 10 * lines - 5 * aggregate - 7 * holes - 3 * bumpiness
