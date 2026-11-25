"""Hard-drop simulation. The caller's board is not modified."""

from __future__ import annotations

from game.board import Board, clear_lines, copy_board, landing_row, place
from game.constants import COLS
from game.pieces import piece_width, rotation_count


def simulate_drop(
    board: Board,
    piece_id: int,
    rotation: int,
    col: int,
) -> tuple[Board, int] | None:
    """Copy the board, hard-drop from the top, lock, and clear.

    `col` is the column of the piece's leftmost block. Returns the new board
    and the number of lines cleared, or None when the pose does not fit at the
    top of the well.
    """
    row = landing_row(board, piece_id, rotation, col, 0)
    if row is None:
        return None
    landed = copy_board(board)
    place(landed, piece_id, rotation, row, col)
    cleared = clear_lines(landed)
    return landed, cleared


def iter_drops(board: Board, piece_id: int):
    """Yield every legal (rotation, col, board, lines) hard drop."""
    for rotation in range(rotation_count(piece_id)):
        width = piece_width(piece_id, rotation)
        for col in range(COLS - width + 1):
            dropped = simulate_drop(board, piece_id, rotation, col)
            if dropped is not None:
                yield rotation, col, dropped[0], dropped[1]
