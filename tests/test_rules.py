"""Rules: shapes, collision, clears, scoring, and the live engine."""

from __future__ import annotations

import random
from pathlib import Path

from game.board import clear_lines, copy_board, empty_board, fits
from game.constants import COLS, ROWS, line_score
from game.engine import Game
from game.pieces import I, J, L, O, S, SHAPES, T, Z, draw_piece, rotation_count

EXPECTED_SHAPES = {
    I: (
        ((0, 0), (0, 1), (0, 2), (0, 3)),
        ((0, 0), (1, 0), (2, 0), (3, 0)),
    ),
    O: (((0, 0), (0, 1), (1, 0), (1, 1)),),
    T: (
        ((0, 1), (1, 0), (1, 1), (1, 2)),
        ((0, 0), (1, 0), (1, 1), (2, 0)),
        ((0, 0), (0, 1), (0, 2), (1, 1)),
        ((0, 1), (1, 0), (1, 1), (2, 1)),
    ),
    S: (
        ((0, 1), (0, 2), (1, 0), (1, 1)),
        ((0, 0), (1, 0), (1, 1), (2, 1)),
    ),
    Z: (
        ((0, 0), (0, 1), (1, 1), (1, 2)),
        ((0, 1), (1, 0), (1, 1), (2, 0)),
    ),
    J: (
        ((0, 0), (1, 0), (1, 1), (1, 2)),
        ((0, 0), (0, 1), (1, 0), (2, 0)),
        ((0, 0), (0, 1), (0, 2), (1, 2)),
        ((0, 1), (1, 1), (2, 0), (2, 1)),
    ),
    L: (
        ((0, 2), (1, 0), (1, 1), (1, 2)),
        ((0, 0), (1, 0), (2, 0), (2, 1)),
        ((0, 0), (0, 1), (0, 2), (1, 0)),
        ((0, 0), (0, 1), (1, 1), (2, 1)),
    ),
}


def test_piece_ids_and_normalized_shapes():
    assert (I, O, T, S, Z, J, L) == (1, 2, 3, 4, 5, 6, 7)
    assert rotation_count(I) == 2
    assert rotation_count(O) == 1
    assert rotation_count(T) == 4
    assert rotation_count(S) == 2
    assert rotation_count(Z) == 2
    assert rotation_count(J) == 4
    assert rotation_count(L) == 4
    for piece_id, rotations in EXPECTED_SHAPES.items():
        assert SHAPES[piece_id] == rotations
        for shape in rotations:
            assert len(shape) == 4
            assert len(set(shape)) == 4
            assert min(row for row, _ in shape) == 0
            assert min(col for _, col in shape) == 0


def test_draw_piece_is_deterministic_and_uniform_over_ids():
    first = [draw_piece(random.Random(4)) for _ in range(1)]
    again = [draw_piece(random.Random(4)) for _ in range(1)]
    assert first == again
    seen = {draw_piece(random.Random(i)) for i in range(200)}
    assert seen == {1, 2, 3, 4, 5, 6, 7}


def test_line_score_table():
    assert line_score(0) == 0
    assert [line_score(n) for n in (1, 2, 3, 4)] == [100, 300, 500, 800]


def test_clear_lines_shifts_survivors_down():
    board = empty_board()
    for col in range(COLS):
        board[18][col] = 1
        board[19][col] = 2
    board[17][0] = 3
    assert clear_lines(board) == 2
    assert board[19][0] == 3
    assert all(board[19][col] == 0 for col in range(1, COLS))
    assert all(cell == 0 for row in board[:19] for cell in row)


def test_clear_lines_leaves_a_partial_board_alone():
    board = empty_board()
    board[19][0] = 1
    before = copy_board(board)
    assert clear_lines(board) == 0
    assert board == before


def test_fits_rejects_walls_and_blocks():
    board = empty_board()
    assert fits(board, I, 0, 0, 0)
    assert not fits(board, I, 0, 0, 7)
    assert not fits(board, I, 1, 17, 0)
    board[19][0] = 1
    assert not fits(board, O, 0, 18, 0)


def test_engine_matches_piece_sequence():
    rng = random.Random(4)
    game = Game(4)
    for _ in range(12):
        assert game.piece_id == draw_piece(rng)
        assert game.hard_drop() == "lock"


def test_move_and_rejected_rotation():
    game = Game(0)
    game.piece_id = T
    game.rotation = 0
    game.row = 0
    game.col = 0
    assert game.move(-1) is False
    assert game.col == 0
    assert game.move(1) is True
    game.col = 0
    game.board[2][0] = 1
    assert game.current_fits()
    assert game.rotate() is False
    assert game.rotation == 0


def test_single_double_and_tetris_scores():
    single = Game(0)
    single.piece_id = I
    single.rotation = 0
    single.col = 0
    single.row = 0
    for col in range(4, COLS):
        single.board[19][col] = T
    assert single.hard_drop() == "lock"
    assert (single.lines, single.score, single.pieces) == (1, 100, 1)
    assert all(cell == 0 for row in single.board for cell in row)

    double = Game(0)
    double.piece_id = O
    double.rotation = 0
    double.col = 0
    double.row = 0
    for row in (18, 19):
        for col in range(2, COLS):
            double.board[row][col] = T
    assert double.hard_drop() == "lock"
    assert (double.lines, double.score) == (2, 300)

    tetris = Game(0)
    tetris.piece_id = I
    tetris.rotation = 1
    tetris.col = 0
    tetris.row = 0
    for row in range(16, 20):
        for col in range(1, COLS):
            tetris.board[row][col] = O
    assert tetris.hard_drop() == "lock"
    assert (tetris.lines, tetris.score, tetris.pieces) == (4, 800, 1)
    assert all(cell == 0 for row in tetris.board for cell in row)


def test_soft_drop_matches_hard_drop():
    hard = Game(1)
    soft = Game(1)
    hard.col = 0
    soft.col = 0
    hard.hard_drop()
    while soft.pieces == 0:
        soft.soft_drop()
    assert soft.board == hard.board
    assert (soft.score, soft.lines, soft.piece_id) == (hard.score, hard.lines, hard.piece_id)


def test_rules_package_has_no_pygame_or_agent_imports():
    root = Path(__file__).resolve().parents[1] / "game"
    for path in root.glob("*.py"):
        text = path.read_text(encoding="utf-8")
        assert "pygame" not in text
        assert "import ai" not in text
        assert "from ai" not in text
    assert empty_board() and ROWS == 20 and COLS == 10
