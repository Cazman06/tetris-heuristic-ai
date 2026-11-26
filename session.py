"""Live session shared by the window.

Human death is a blocked spawn. Agent death is an empty move list. The two
are different: the center columns can be blocked while a side drop still fits.
"""

from __future__ import annotations

from ai.agents import HeightAgent, HeuristicAgent, Placement, RandomAgent
from game.board import Board
from game.engine import Game

MODES = ("human", "heuristic", "random", "height")

MODE_LABELS = {
    "human": "Human",
    "heuristic": "Heuristic",
    "random": "Random",
    "height": "Height-only",
}

# How the window feels. The benchmark does not use these clocks.
GRAVITY_MS = 800
SOFT_MS = 40
LOCK_MS = 500


class Session:
    def __init__(self, seed: int, ai: bool = False) -> None:
        self.seed = seed
        self.mode = "heuristic" if ai else "human"
        self.game = Game(seed)
        self.agents = {
            "heuristic": HeuristicAgent(),
            "height": HeightAgent(),
            "random": RandomAgent(seed),
        }
        self.decision: Placement | None = None
        self.lock_ms: int | None = None
        self.gravity_ms = 0
        self.prepare()

    def restart(self) -> None:
        self.game.reset()
        self.agents["random"].reset()
        self.decision = None
        self.prepare()

    def set_mode(self, mode: str) -> None:
        if mode not in MODES:
            raise ValueError(mode)
        if mode == self.mode:
            return
        self.mode = mode
        self.prepare()

    def prepare(self) -> None:
        """Apply the mode's rule to the piece that was just spawned."""
        self.lock_ms = None
        self.gravity_ms = 0
        if self.game.game_over:
            self.decision = None
            return
        agent = self._agent()
        if agent is None:
            self.decision = None
            if not self.game.current_fits():
                self.game.game_over = True
            return
        decision = agent.select(self.game.board, self.game.piece_id)
        if decision is None:
            self.decision = None
            self.game.game_over = True
            return
        self.decision = decision
        self.game.rotation = decision.rotation
        self.game.col = decision.col
        self.game.row = 0
        if not self.game.current_fits():
            self.game.game_over = True

    def _human_turn(self) -> bool:
        return self.mode == "human" and not self.game.game_over

    def human_move(self, dc: int) -> bool:
        if not self._human_turn():
            return False
        moved = self.game.move(dc)
        if not moved:
            return False
        self._after_shift()
        return True

    def human_rotate(self) -> bool:
        if not self._human_turn():
            return False
        rotated = self.game.rotate()
        if not rotated:
            return False
        self._after_shift()
        return True

    def human_soft_drop(self) -> None:
        """One immediate soft-drop step from a key press."""
        if not self._human_turn():
            return
        self.gravity_ms = 0
        self._descend()

    def human_hard_drop(self) -> None:
        if not self._human_turn():
            return
        self._commit_lock()

    def tick_human(self, dt: int, soft: bool = False) -> None:
        if not self._human_turn():
            return
        if self.lock_ms is not None:
            self.lock_ms += dt
            if self.lock_ms >= LOCK_MS:
                self._commit_lock()
            return
        self.gravity_ms += dt
        interval = SOFT_MS if soft else GRAVITY_MS
        if self.gravity_ms >= interval:
            self.gravity_ms = 0
            self._descend()

    def ai_fall_once(self) -> str:
        """Drop the planned pose one row. Locks immediately on contact."""
        if self.mode == "human" or self.game.game_over:
            return "idle"
        result = self.game.soft_drop()
        if result == "lock":
            self.prepare()
        return result

    def _agent(self):
        return self.agents.get(self.mode)

    def _after_shift(self) -> None:
        if self.game.current_fits(row=self.game.row + 1):
            self.lock_ms = None
        elif self.lock_ms is not None:
            self.lock_ms = 0

    def _descend(self) -> None:
        if self.game.current_fits(row=self.game.row + 1):
            self.game.row += 1
            self.lock_ms = None
        elif self.lock_ms is None:
            self.lock_ms = 0

    def _commit_lock(self) -> None:
        self.lock_ms = None
        self.gravity_ms = 0
        result = self.game.hard_drop()
        if result == "lock":
            self.prepare()

    @property
    def board(self) -> Board:
        return self.game.board
