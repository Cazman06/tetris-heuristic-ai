"""Live game: spawn, move, rotate, gravity step, hard drop, lock, score.

This module does not decide that the game is over. A human dies when the
spawn pose overlaps the stack. An agent dies when it has no legal hard drop,
which can still be true after a blocked center spawn. The session applies
the rule that matches the current player.
"""

from __future__ import annotations

import random

from game.board import Board, empty_board, fits, landing_row, place, clear_lines
from game.constants import COLS, line_score
from game.pieces import cells, draw_piece, piece_width, rotation_count


class Game:
    def __init__(self, seed: int) -> None:
        self.seed = seed
        self.rng = random.Random(seed)
        self.board: Board = empty_board()
        self.score = 0
        self.lines = 0
        self.pieces = 0
        self.game_over = False
        self.piece_id = 1
        self.rotation = 0
        self.row = 0
        self.col = 0
        self.reset()

    def reset(self) -> None:
        self.rng = random.Random(self.seed)
        self.board = empty_board()
        self.score = 0
        self.lines = 0
        self.pieces = 0
        self.game_over = False
        self._spawn()

    def _spawn(self) -> None:
        self.piece_id = draw_piece(self.rng)
        self.rotation = 0
        self.col = (COLS - piece_width(self.piece_id, 0)) // 2
        self.row = 0

    def current_fits(
        self,
        rotation: int | None = None,
        row: int | None = None,
        col: int | None = None,
    ) -> bool:
        return fits(
            self.board,
            self.piece_id,
            self.rotation if rotation is None else rotation,
            self.row if row is None else row,
            self.col if col is None else col,
        )

    def current_cells(self) -> list[tuple[int, int]]:
        return cells(self.piece_id, self.rotation, self.row, self.col)

    def ghost_cells(self) -> list[tuple[int, int]]:
        row = landing_row(self.board, self.piece_id, self.rotation, self.col, self.row)
        if row is None or row == self.row:
            return []
        return cells(self.piece_id, self.rotation, row, self.col)

    def move(self, dc: int) -> bool:
        if self.game_over:
            return False
        if self.current_fits(col=self.col + dc):
            self.col += dc
            return True
        return False

    def rotate(self) -> bool:
        """Clockwise. The origin stays put, and a collision rejects the turn."""
        if self.game_over:
            return False
        new_rotation = (self.rotation + 1) % rotation_count(self.piece_id)
        if self.current_fits(rotation=new_rotation):
            self.rotation = new_rotation
            return True
        return False

    def soft_drop(self) -> str:
        """Drop one row, or lock if the next row is blocked.

        Returns "fall", "lock", or "idle". Locking is immediate: this is the
        primitive the agent animation uses. Human play adds lock delay above it.
        """
        if self.game_over:
            return "idle"
        if self.current_fits(row=self.row + 1):
            self.row += 1
            return "fall"
        self._lock()
        return "lock"

    def hard_drop(self) -> str:
        """Fall straight down from the current row and lock."""
        if self.game_over:
            return "idle"
        row = landing_row(self.board, self.piece_id, self.rotation, self.col, self.row)
        if row is None:
            return "idle"
        self.row = row
        self._lock()
        return "lock"

    def _lock(self) -> None:
        place(self.board, self.piece_id, self.rotation, self.row, self.col)
        cleared = clear_lines(self.board)
        self.lines += cleared
        self.score += line_score(cleared)
        self.pieces += 1
        self._spawn()
