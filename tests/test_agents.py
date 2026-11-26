"""Search, features, and agreement between the live engine and the benchmark."""

from __future__ import annotations

from pathlib import Path

from ai.agents import (
    HeightAgent,
    HeuristicAgent,
    Placement,
    RandomAgent,
    all_placements,
    height_rank,
    heuristic_rank,
    pick_best,
)
from ai.features import W_BUMP, W_HEIGHT, W_HOLES, W_LINES, heuristic_value, measure
from ai.simulate import simulate_drop
from evaluation.benchmark import format_report, make_agent, play_game, run_benchmark
from game.board import copy_board, empty_board
from game.constants import COLS, ROWS
from game.engine import Game
from game.pieces import I, T
from session import LOCK_MS, Session


def _placement(rotation: int, col: int, lines: int = 0, aggregate: int = 0, holes: int = 0, bump: int = 0):
    return Placement(rotation, col, lines, aggregate, holes, bump, candidates=1)


def test_penalty_order_matches_the_weights():
    assert (W_LINES, W_HEIGHT, W_HOLES, W_BUMP) == (1.0, 0.5, 0.7, 0.3)
    assert round(10 * W_LINES) == 10
    assert round(10 * W_HEIGHT) == 5
    assert round(10 * W_HOLES) == 7
    assert round(10 * W_BUMP) == 3
    hole = heuristic_value(0, 0, 1, 0)
    height = heuristic_value(0, 1, 0, 0)
    bump = heuristic_value(0, 0, 0, 1)
    assert hole < height < bump < 0
    assert heuristic_value(1, 0, 0, 0) == 10
    assert heuristic_value(0, 4, 0, 1) == -23


def test_holes_height_and_wall_bumpiness():
    board = empty_board()
    for row in (17, 18, 19):
        board[row][0] = I
    board[17][1] = I
    board[19][1] = I
    aggregate, holes, bump = measure(board)
    assert (aggregate, holes, bump) == (6, 1, 3)

    def stack(col: int) -> list[list[int]]:
        stacked = empty_board()
        for offset in range(4):
            stacked[ROWS - 1 - offset][col] = I
        return stacked

    assert measure(stack(0))[2] == 4
    assert measure(stack(5))[2] == 8


def test_simulate_drop_does_not_mutate_and_can_clear():
    board = empty_board()
    for col in range(4, COLS):
        board[19][col] = T
    original = copy_board(board)
    dropped = simulate_drop(board, I, 0, 0)
    assert dropped is not None
    landed, lines = dropped
    assert lines == 1
    assert board == original
    assert all(cell == 0 for row in landed for cell in row)


def test_empty_well_move_counts():
    counts = [len(all_placements(empty_board(), piece_id)) for piece_id in range(1, 8)]
    assert counts == [17, 9, 34, 17, 17, 34, 34]


def test_full_board_has_no_move():
    board = [[1] * COLS for _ in range(ROWS)]
    assert HeuristicAgent().select(board, I) is None
    assert HeightAgent().select(board, I) is None
    assert RandomAgent(0).select(board, I) is None


def test_heuristic_and_height_take_the_clear():
    board = empty_board()
    for col in range(4, COLS):
        board[19][col] = T
    for agent in (HeuristicAgent(), HeightAgent()):
        placement = agent.select(board, I)
        assert placement is not None
        assert (placement.rotation, placement.col, placement.lines) == (0, 0, 1)


def test_ties_keep_the_earlier_move():
    first = _placement(0, 0, aggregate=5)
    second = _placement(0, 1, aggregate=5)
    better = _placement(1, 4, aggregate=4)
    assert pick_best([first, second], height_rank) is first
    assert pick_best([first, second, better], height_rank) is better
    assert pick_best([first, better], heuristic_rank) is better


def test_random_agent_replays_its_seed():
    board = empty_board()
    one = RandomAgent(7).select(board, T)
    two = RandomAgent(7).select(board, T)
    assert one == two
    assert one is not None and one.candidates == 34


def test_engine_matches_benchmark_search():
    for name in ("random", "height", "heuristic"):
        for seed in range(3):
            played = play_game(make_agent(name, seed), seed, max_pieces=40)
            game = Game(seed)
            agent = make_agent(name, seed)
            while game.pieces < 40:
                placement = agent.select(game.board, game.piece_id)
                if placement is None:
                    break
                game.rotation = placement.rotation
                game.col = placement.col
                game.row = 0
                assert game.current_fits()
                assert game.hard_drop() == "lock"
            assert (game.score, game.lines, game.pieces) == (
                played.score,
                played.lines,
                played.pieces,
            )


def test_short_games_stop_at_the_cap():
    result = play_game(HeuristicAgent(), 0, max_pieces=5)
    assert result.pieces == 5
    assert result.capped


def test_report_explains_weights_and_limits():
    from evaluation.benchmark import GameResult

    def result(score: int, lines: int, pieces: int) -> GameResult:
        return GameResult(score, lines, pieces, capped=False)

    results = {
        "random": [result(0, 0, 10), result(0, 0, 12)],
        "height": [result(100, 1, 20), result(300, 2, 22)],
        "heuristic": [result(800, 4, 40), result(100, 1, 30)],
    }
    text = format_report(results, 10000)
    assert "H(s) = 1.0*L - 0.5*A - 0.7*holes - 0.3*B" in text
    assert "B = 4" in text
    assert "B = 8" in text
    assert "800" in text
    assert "next piece" in text
    assert "No game hit the 10,000-piece cap." in text
    assert "On every seed, pieces placed rank heuristic, then height-only, then random." in text


def test_benchmark_module_runs_a_short_pair():
    results = run_benchmark(seeds=1, max_pieces=15)
    assert results["heuristic"][0].pieces == 15
    assert results["heuristic"][0].capped
    text = format_report(results, 15)
    assert "Heuristic" in text


def test_spawn_block_kills_a_human_and_not_an_agent():
    blocked = ((0, 4), (0, 5), (1, 4), (1, 5))

    human = Session(0, ai=False)
    human.game.piece_id = 2  # O, spawn column 4
    human.game.rotation = 0
    human.game.row = 0
    human.game.col = 4
    for row, col in blocked:
        human.game.board[row][col] = 1
    human.prepare()
    assert human.game.game_over

    agent = Session(0, ai=True)
    agent.game.piece_id = 2
    for row, col in blocked:
        agent.game.board[row][col] = 1
    agent.prepare()
    assert not agent.game.game_over
    assert agent.decision is not None
    assert agent.decision.col != 4


def test_human_lock_delay_and_ai_immediate_lock():
    human = Session(0, ai=False)
    for _ in range(30):
        if human.lock_ms is not None:
            break
        human.human_soft_drop()
    assert human.lock_ms == 0
    assert human.game.pieces == 0
    human.tick_human(LOCK_MS - 1)
    assert human.game.pieces == 0
    human.tick_human(1)
    assert human.game.pieces == 1

    agent = Session(0, ai=True)
    for _ in range(30):
        agent.ai_fall_once()
        if agent.game.pieces == 1:
            break
    assert agent.game.pieces == 1
    assert agent.decision is not None


def test_restart_replays_the_heuristic():
    session = Session(3, ai=True)
    for _ in range(50):
        session.ai_fall_once()
    snapshot = (
        copy_board(session.game.board),
        session.game.pieces,
        session.game.score,
        session.game.piece_id,
        session.game.row,
        session.game.col,
        session.game.rotation,
    )
    session.restart()
    assert session.mode == "heuristic"
    for _ in range(50):
        session.ai_fall_once()
    assert snapshot == (
        session.game.board,
        session.game.pieces,
        session.game.score,
        session.game.piece_id,
        session.game.row,
        session.game.col,
        session.game.rotation,
    )


def test_search_modules_do_not_import_pygame():
    root = Path(__file__).resolve().parents[1]
    for folder in ("ai", "evaluation"):
        for path in (root / folder).glob("*.py"):
            assert "pygame" not in path.read_text(encoding="utf-8")
    assert "pygame" not in (root / "session.py").read_text(encoding="utf-8")
