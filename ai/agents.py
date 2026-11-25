"""One ply of informed search, plus the two baselines.

Successors are the legal hard drops of the current piece. A heuristic ranks
the boards those drops leave behind. The agent then plays the best one. It
does not see the next piece.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, replace

from ai.features import heuristic_value, measure, published_h
from ai.simulate import iter_drops
from game.board import Board


@dataclass(frozen=True)
class Placement:
    rotation: int
    col: int
    lines: int
    aggregate_height: int
    holes: int
    bumpiness: int
    candidates: int

    @property
    def heuristic(self) -> float:
        return published_h(self.lines, self.aggregate_height, self.holes, self.bumpiness)


def all_placements(board: Board, piece_id: int) -> list[Placement]:
    found: list[Placement] = []
    for rotation, col, new_board, lines in iter_drops(board, piece_id):
        aggregate, holes, bumpiness = measure(new_board)
        found.append(
            Placement(
                rotation=rotation,
                col=col,
                lines=lines,
                aggregate_height=aggregate,
                holes=holes,
                bumpiness=bumpiness,
                candidates=0,
            )
        )
    count = len(found)
    if count == 0:
        return []
    return [replace(item, candidates=count) for item in found]


def pick_best(options: list[Placement], rank) -> Placement | None:
    """Highest rank. Ties keep the earliest rotation, then the leftmost column."""
    best: Placement | None = None
    best_rank: int | None = None
    for option in options:
        value = rank(option)
        if best_rank is None or value > best_rank:
            best = option
            best_rank = value
    return best


def heuristic_rank(placement: Placement) -> int:
    return heuristic_value(
        placement.lines,
        placement.aggregate_height,
        placement.holes,
        placement.bumpiness,
    )


def height_rank(placement: Placement) -> int:
    """Height-only policy: minimize aggregate height. Clears help only by lowering it."""
    return -placement.aggregate_height


class HeuristicAgent:
    name = "heuristic"
    label = "Heuristic"

    def select(self, board: Board, piece_id: int) -> Placement | None:
        return pick_best(all_placements(board, piece_id), heuristic_rank)


class HeightAgent:
    name = "height"
    label = "Height-only"

    def select(self, board: Board, piece_id: int) -> Placement | None:
        return pick_best(all_placements(board, piece_id), height_rank)


class RandomAgent:
    name = "random"
    label = "Random"

    def __init__(self, seed: int) -> None:
        self.seed = seed
        self.rng = random.Random(seed)

    def reset(self) -> None:
        self.rng = random.Random(self.seed)

    def select(self, board: Board, piece_id: int) -> Placement | None:
        options = all_placements(board, piece_id)
        if not options:
            return None
        return self.rng.choice(options)
