"""The seven tetrominoes.

Each rotation is a tuple of (row, col) cells. Row 0 of a shape is its top,
column 0 is its leftmost block, and rotations go clockwise. There are no wall
kicks: a rotation that overlaps a block or the wall is rejected by the caller.
"""

from __future__ import annotations

import random

I, O, T, S, Z, J, L = 1, 2, 3, 4, 5, 6, 7

PIECE_NAMES = {
    I: "I",
    O: "O",
    T: "T",
    S: "S",
    Z: "Z",
    J: "J",
    L: "L",
}

# Index 0 is unused so a cell value is the piece id.
SHAPES: tuple[tuple[tuple[tuple[int, int], ...], ...], ...] = (
    (),
    (  # I
        ((0, 0), (0, 1), (0, 2), (0, 3)),
        ((0, 0), (1, 0), (2, 0), (3, 0)),
    ),
    (  # O
        ((0, 0), (0, 1), (1, 0), (1, 1)),
    ),
    (  # T
        ((0, 1), (1, 0), (1, 1), (1, 2)),
        ((0, 0), (1, 0), (1, 1), (2, 0)),
        ((0, 0), (0, 1), (0, 2), (1, 1)),
        ((0, 1), (1, 0), (1, 1), (2, 1)),
    ),
    (  # S
        ((0, 1), (0, 2), (1, 0), (1, 1)),
        ((0, 0), (1, 0), (1, 1), (2, 1)),
    ),
    (  # Z
        ((0, 0), (0, 1), (1, 1), (1, 2)),
        ((0, 1), (1, 0), (1, 1), (2, 0)),
    ),
    (  # J
        ((0, 0), (1, 0), (1, 1), (1, 2)),
        ((0, 0), (0, 1), (1, 0), (2, 0)),
        ((0, 0), (0, 1), (0, 2), (1, 2)),
        ((0, 1), (1, 1), (2, 0), (2, 1)),
    ),
    (  # L
        ((0, 2), (1, 0), (1, 1), (1, 2)),
        ((0, 0), (1, 0), (2, 0), (2, 1)),
        ((0, 0), (0, 1), (0, 2), (1, 0)),
        ((0, 0), (0, 1), (1, 1), (2, 1)),
    ),
)


def draw_piece(rng: random.Random) -> int:
    """Draw one piece id. Pieces are i.i.d. uniform, not a 7-bag."""
    return 1 + rng.randrange(7)


def rotation_count(piece_id: int) -> int:
    return len(SHAPES[piece_id])


def piece_width(piece_id: int, rotation: int) -> int:
    return max(col for _, col in SHAPES[piece_id][rotation]) + 1


def cells(piece_id: int, rotation: int, row: int, col: int) -> list[tuple[int, int]]:
    """Absolute cells when the shape's top-left block origin is at (row, col)."""
    return [(row + dr, col + dc) for dr, dc in SHAPES[piece_id][rotation]]
