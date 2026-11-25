"""Locked-board operations. Row 0 is the top. 0 is empty."""

from __future__ import annotations

from game.constants import COLS, EMPTY, ROWS
from game.pieces import SHAPES

Board = list[list[int]]


def empty_board() -> Board:
    return [[EMPTY] * COLS for _ in range(ROWS)]


def copy_board(board: Board) -> Board:
    return [row[:] for row in board]


def fits(board: Board, piece_id: int, rotation: int, row: int, col: int) -> bool:
    """True when every cell is inside the well and on an empty square."""
    for dr, dc in SHAPES[piece_id][rotation]:
        r = row + dr
        c = col + dc
        if r < 0 or c < 0 or r >= ROWS or c >= COLS or board[r][c] != EMPTY:
            return False
    return True


def landing_row(
    board: Board,
    piece_id: int,
    rotation: int,
    col: int,
    start_row: int = 0,
) -> int | None:
    """Lowest row this pose can fall to, starting at `start_row`.

    Returns None when the pose does not fit at the start row. The piece stops
    at the first collision; it does not pass through blocks.
    """
    if not fits(board, piece_id, rotation, start_row, col):
        return None
    row = start_row
    while fits(board, piece_id, rotation, row + 1, col):
        row += 1
    return row


def place(board: Board, piece_id: int, rotation: int, row: int, col: int) -> None:
    for dr, dc in SHAPES[piece_id][rotation]:
        board[row + dr][col + dc] = piece_id


def clear_lines(board: Board) -> int:
    """Remove full rows, shift the rest down, and return how many were removed."""
    kept = [row for row in board if any(cell == EMPTY for cell in row)]
    cleared = ROWS - len(kept)
    if cleared == 0:
        return 0
    board[:] = [[EMPTY] * COLS for _ in range(cleared)] + kept
    return cleared
