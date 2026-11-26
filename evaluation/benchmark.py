"""Paired measurement of random, height-only, and the four-feature heuristic.

Run from the project root:

    python -m evaluation.benchmark
"""

from __future__ import annotations

import argparse
import random
import sys
from dataclasses import dataclass

from ai.agents import HeightAgent, HeuristicAgent, RandomAgent
from ai.features import FORMULA, measure
from ai.simulate import simulate_drop
from game.board import empty_board
from game.constants import MAX_PIECES, ROWS, line_score
from game.pieces import draw_piece


AGENT_ORDER = ("random", "height", "heuristic")
AGENT_LABELS = {
    "random": "Random",
    "height": "Height-only",
    "heuristic": "Heuristic",
}


@dataclass(frozen=True)
class GameResult:
    score: int
    lines: int
    pieces: int
    capped: bool


def make_agent(name: str, seed: int):
    match name:
        case "random":
            return RandomAgent(seed)
        case "height":
            return HeightAgent()
        case "heuristic":
            return HeuristicAgent()
        case _:
            raise ValueError(name)


def play_game(agent, seed: int, max_pieces: int = MAX_PIECES) -> GameResult:
    """Play one agent on one piece seed. The piece RNG is not the agent's RNG."""
    rng = random.Random(seed)
    board = empty_board()
    score = 0
    lines_total = 0
    pieces = 0
    while pieces < max_pieces:
        piece_id = draw_piece(rng)
        placement = agent.select(board, piece_id)
        if placement is None:
            break
        dropped = simulate_drop(board, piece_id, placement.rotation, placement.col)
        if dropped is None:
            break
        board, cleared = dropped
        pieces += 1
        lines_total += cleared
        score += line_score(cleared)
    return GameResult(
        score=score,
        lines=lines_total,
        pieces=pieces,
        capped=pieces >= max_pieces,
    )


def run_benchmark(seeds: int = 20, max_pieces: int = MAX_PIECES, progress=None):
    results = {name: [] for name in AGENT_ORDER}
    for seed in range(seeds):
        for name in AGENT_ORDER:
            results[name].append(play_game(make_agent(name, seed), seed, max_pieces))
        if progress is not None:
            progress(seed, results)
    return results


def _stack(col: int, height: int):
    board = empty_board()
    for offset in range(height):
        board[ROWS - 1 - offset][col] = 1
    return board


def _mean(values: list[int]) -> float:
    return sum(values) / len(values)


def _format_score_mean(values: list[int]) -> str:
    mean = _mean(values)
    if abs(mean - round(mean)) < 1e-9:
        return f"{round(mean):,}"
    return f"{mean:,.1f}"


def _format_decimal(values: list[int]) -> str:
    return f"{_mean(values):,.1f}"


def _rows(headers: list[str], rows: list[list[str]]) -> str:
    widths = [len(header) for header in headers]
    for row in rows:
        for index, cell in enumerate(row):
            widths[index] = max(widths[index], len(cell))
    def line(cells: list[str]) -> str:
        parts = []
        for index, cell in enumerate(cells):
            if index == 0:
                parts.append(cell.ljust(widths[index]))
            else:
                parts.append(cell.rjust(widths[index]))
        return "  ".join(parts)
    body = [line(headers), line(["-" * width for width in widths])]
    body.extend(line(row) for row in rows)
    return "\n".join(body)


def format_report(results: dict[str, list[GameResult]], max_pieces: int) -> str:
    n = len(results["heuristic"])
    seed_text = "seed 0" if n == 1 else f"seeds 0-{n - 1}"
    _, _, bump_wall = measure(_stack(0, 4))
    _, _, bump_center = measure(_stack(5, 4))

    summary = [
        [
            "Average score",
            _format_score_mean([item.score for item in results["random"]]),
            _format_score_mean([item.score for item in results["height"]]),
            _format_score_mean([item.score for item in results["heuristic"]]),
        ],
        [
            "Average lines",
            _format_decimal([item.lines for item in results["random"]]),
            _format_decimal([item.lines for item in results["height"]]),
            _format_decimal([item.lines for item in results["heuristic"]]),
        ],
        [
            "Average pieces placed",
            _format_decimal([item.pieces for item in results["random"]]),
            _format_decimal([item.pieces for item in results["height"]]),
            _format_decimal([item.pieces for item in results["heuristic"]]),
        ],
        [
            "Best pieces placed",
            f"{max(item.pieces for item in results['random']):,}",
            f"{max(item.pieces for item in results['height']):,}",
            f"{max(item.pieces for item in results['heuristic']):,}",
        ],
    ]

    per_seed = []
    ordered = 0
    for index in range(n):
        random_pieces = results["random"][index].pieces
        height_pieces = results["height"][index].pieces
        heuristic_pieces = results["heuristic"][index].pieces
        if heuristic_pieces > height_pieces > random_pieces:
            ordered += 1
        per_seed.append(
            [
                str(index),
                f"{random_pieces:,}",
                f"{height_pieces:,}",
                f"{heuristic_pieces:,}",
            ]
        )

    heuristic_pieces = [item.pieces for item in results["heuristic"]]
    capped = [
        f"{AGENT_LABELS[name]} seed {index}"
        for name in AGENT_ORDER
        for index, item in enumerate(results[name])
        if item.capped
    ]
    if capped:
        cap_line = "Hit the piece cap: " + ", ".join(capped) + "."
    else:
        cap_line = f"No game hit the {max_pieces:,}-piece cap."

    if ordered == n:
        order_line = (
            "On every seed, pieces placed rank heuristic, then height-only, then random."
        )
    else:
        order_line = (
            f"Pieces placed rank heuristic, then height-only, then random "
            f"on {ordered} of {n} seeds."
        )

    lines = [
        "One-ply heuristic Tetris",
        "",
        "Decision path",
        "  The agent sees the current piece and the locked board. It does not see the next piece.",
        "  1. Enumerate every rotation and every leftmost column.",
        "  2. Hard-drop that pose from the top of the well. There are no wall kicks.",
        "     A pose that overlaps a block or leaves the well is discarded.",
        "  3. Copy the board, lock the piece, and clear full rows. The live game is unchanged.",
        "  4. Score the result. L is the number of rows removed. A, holes, and B are measured",
        "     after the clear, because those rows are gone.",
        "  5. Play the highest score. An equal score keeps the earliest rotation, then the",
        "     leftmost column.",
        "  6. Spawn the next piece. Stop when no legal drop remains, or at the piece cap.",
        "",
        "Weights",
        f"  {FORMULA}",
        "  L      lines cleared by this drop",
        "  A      sum of column heights (highest block in each column, empty columns are 0)",
        "  holes  empty cells with a block above them in the same column",
        "  B      sum of absolute height gaps between neighboring columns",
        "  A clear is the reward. Per unit, holes are the strongest penalty, then height,",
        "  then roughness. These weights were not fit by a search.",
        "  Height-only minimizes A and ignores L, holes, and B.",
        "  Random chooses uniformly among the legal drops.",
        "  The game score is separate: 100, 300, 500, and 800 for one to four lines.",
        "",
        "Paired measurement",
        f"  {seed_text}. Cap {max_pieces:,} pieces. Same piece seeds for every agent.",
        "  Pieces placed is survival: a hard drop has no real-time clock.",
        "",
        _rows(["Metric", "Random", "Height-only", "Heuristic"], summary),
        "",
        order_line,
        (
            f"Heuristic survival runs from {min(heuristic_pieces):,} "
            f"to {max(heuristic_pieces):,} pieces."
        ),
        cap_line,
        "",
        "Pieces placed by seed",
        _rows(["seed", "random", "height-only", "heuristic"], per_seed),
        "",
        "Limits",
        "  This is one ply. The next piece is unknown, so the search cannot set up a well for it.",
        "  Multi-ply search, Monte Carlo tree search, reinforcement learning, and a search",
        "  over these weights are later.",
        "  Bumpiness treats a stack against the wall as smoother than the same stack in the",
        f"  center. A height-4 stack in column 0 has B = {bump_wall}. The same stack in",
        f"  column 5 has B = {bump_center}.",
        "  The score table pays extra for a four-line clear (800) that H counts as four",
        "  ordinary lines. Four separate one-line clears score 400 and also have L = 4.",
        "",
    ]
    return "\n".join(lines)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Compare Tetris agents on shared piece seeds.")
    parser.add_argument("--seeds", type=int, default=20, help="paired seeds, starting at 0")
    parser.add_argument("--max-pieces", type=int, default=MAX_PIECES, help="survival cap")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)

    def progress(seed: int, results) -> None:
        random_pieces = results["random"][-1].pieces
        height_pieces = results["height"][-1].pieces
        heuristic_pieces = results["heuristic"][-1].pieces
        print(
            f"seed {seed}: random {random_pieces}, height-only {height_pieces}, "
            f"heuristic {heuristic_pieces}",
            file=sys.stderr,
        )

    results = run_benchmark(args.seeds, args.max_pieces, progress)
    print(format_report(results, args.max_pieces))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
