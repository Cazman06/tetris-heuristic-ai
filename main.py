"""Tetris window: a well and a side panel.

    python main.py                 # human
    python main.py --ai --seed 4   # watch the heuristic

Arrows move, Up rotates, Down soft-drops, Space hard-drops.
A, N, H, and P switch among the heuristic, random, height-only, and human.
R restarts the same piece seed.
"""

from __future__ import annotations

import argparse
import os
import random

from game.constants import COLS, ROWS
from game.pieces import PIECE_NAMES
from session import MODE_LABELS, Session

CELL = 32
PAD = 24
GAP = 28
PANEL_W = 320
BOARD_X = PAD
BOARD_Y = PAD
PANEL_X = BOARD_X + COLS * CELL + GAP
WIDTH = PANEL_X + PANEL_W + PAD
HEIGHT = BOARD_Y + ROWS * CELL + PAD

DAS_DELAY = 180
DAS_REPEAT = 50
AI_TICK_MS = 16
AI_ROWS_PER_TICK = 3

BG = (14, 16, 28)
WELL = (8, 10, 20)
GRID = (32, 38, 58)
BORDER = (86, 104, 148)
PANEL = (20, 24, 42)
TEXT = (236, 240, 248)
MUTED = (154, 166, 190)
ACCENT = (126, 196, 255)
GAME_OVER_COLOR = (255, 112, 128)

PIECE_COLORS = {
    1: (0, 210, 210),
    2: (240, 208, 48),
    3: (176, 96, 224),
    4: (72, 200, 96),
    5: (224, 72, 72),
    6: (72, 112, 240),
    7: (240, 148, 48),
}


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Play Tetris, or watch a one-ply heuristic.")
    parser.add_argument("--ai", action="store_true", help="start under the heuristic agent")
    parser.add_argument("--seed", type=int, default=None, help="piece-sequence seed")
    return parser.parse_args(argv)


class App:
    def __init__(self, session: Session) -> None:
        os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
        import pygame

        self.pygame = pygame
        pygame.display.init()
        pygame.font.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("segoeui", 18)
        self.small = pygame.font.SysFont("segoeui", 16)
        self.bold = pygame.font.SysFont("segoeui", 22, bold=True)
        self.big = pygame.font.SysFont("segoeui", 36, bold=True)
        self.session = session
        self.mode_keys = {
            pygame.K_a: "heuristic",
            pygame.K_n: "random",
            pygame.K_h: "height",
            pygame.K_p: "human",
        }
        self.horizontal = {
            pygame.K_LEFT: ("left", -1),
            pygame.K_RIGHT: ("right", 1),
        }
        self.horiz: tuple[str, int, int] | None = None
        self.soft_held = False
        self.ai_ms = 0
        self.ai_hold = True
        self._caption()

    def _caption(self) -> None:
        label = MODE_LABELS[self.session.mode]
        self.pygame.display.set_caption(f"Tetris - {label}")

    def run(self) -> None:
        pygame = self.pygame
        running = True
        while running:
            dt = self.clock.tick(60)
            for event in pygame.event.get():
                match event.type:
                    case pygame.QUIT:
                        running = False
                    case pygame.KEYDOWN:
                        self._keydown(event.key)
                    case pygame.KEYUP:
                        self._keyup(event.key)
            self._update(dt)
            self._draw()
            pygame.display.flip()
        pygame.quit()

    def _keydown(self, key: int) -> None:
        pygame = self.pygame
        if key in self.mode_keys:
            self._set_mode(self.mode_keys[key])
            return
        match key:
            case pygame.K_ESCAPE:
                pygame.event.post(pygame.event.Event(pygame.QUIT))
            case pygame.K_r:
                self._restart()
            case pygame.K_LEFT | pygame.K_RIGHT | pygame.K_UP | pygame.K_DOWN | pygame.K_SPACE:
                self._human_control(key)

    def _human_control(self, key: int) -> None:
        session = self.session
        if session.mode != "human" or session.game.game_over:
            return
        pygame = self.pygame
        match key:
            case pygame.K_LEFT | pygame.K_RIGHT:
                direction, step = self.horizontal[key]
                session.human_move(step)
                self.horiz = (direction, step, 0)
            case pygame.K_UP:
                session.human_rotate()
            case pygame.K_DOWN:
                self.soft_held = True
                session.human_soft_drop()
            case pygame.K_SPACE:
                session.human_hard_drop()

    def _keyup(self, key: int) -> None:
        match key:
            case self.pygame.K_LEFT | self.pygame.K_RIGHT:
                direction, _step = self.horizontal[key]
                if self.horiz is not None and self.horiz[0] == direction:
                    self.horiz = None
            case self.pygame.K_DOWN:
                self.soft_held = False

    def _set_mode(self, mode: str) -> None:
        if mode == self.session.mode:
            return
        self.session.set_mode(mode)
        self.ai_hold = True
        self.ai_ms = 0
        self.horiz = None
        self.soft_held = False
        self._caption()

    def _restart(self) -> None:
        self.session.restart()
        self.ai_hold = True
        self.ai_ms = 0
        self.horiz = None
        self.soft_held = False
        self._caption()

    def _update(self, dt: int) -> None:
        if self.session.game.game_over:
            return
        if self.session.mode == "human":
            self._update_horizontal(dt)
            self.session.tick_human(dt, soft=self.soft_held)
        else:
            self._update_ai(dt)

    def _update_horizontal(self, dt: int) -> None:
        if self.horiz is None:
            return
        direction, step, held = self.horiz
        held += dt
        while held >= DAS_DELAY:
            self.session.human_move(step)
            held -= DAS_REPEAT
        self.horiz = (direction, step, held)

    def _update_ai(self, dt: int) -> None:
        self.ai_ms += dt
        if self.ai_ms < AI_TICK_MS:
            return
        self.ai_ms = 0
        if self.ai_hold:
            self.ai_hold = False
            return
        for _ in range(AI_ROWS_PER_TICK):
            match self.session.ai_fall_once():
                case "fall":
                    continue
                case "lock":
                    self.ai_hold = True
                    break
                case _:
                    break

    def _draw(self) -> None:
        pygame = self.pygame
        screen = self.screen
        screen.fill(BG)
        self._draw_well()
        self._draw_panel()
        if self.session.game.game_over:
            self._draw_game_over()

    def _draw_well(self) -> None:
        pygame = self.pygame
        screen = self.screen
        game = self.session.game
        board_rect = pygame.Rect(BOARD_X, BOARD_Y, COLS * CELL, ROWS * CELL)
        pygame.draw.rect(screen, WELL, board_rect)
        for col in range(COLS + 1):
            x = BOARD_X + col * CELL
            pygame.draw.line(screen, GRID, (x, BOARD_Y), (x, BOARD_Y + ROWS * CELL))
        for row in range(ROWS + 1):
            y = BOARD_Y + row * CELL
            pygame.draw.line(screen, GRID, (BOARD_X, y), (BOARD_X + COLS * CELL, y))
        pygame.draw.rect(screen, BORDER, board_rect, 2)

        for row in range(ROWS):
            for col in range(COLS):
                piece_id = game.board[row][col]
                if piece_id:
                    self._block(row, col, PIECE_COLORS[piece_id], filled=True)

        color = PIECE_COLORS[game.piece_id]
        if game.current_fits():
            for row, col in game.ghost_cells():
                self._block(row, col, color, filled=False)
            for row, col in game.current_cells():
                self._block(row, col, color, filled=True)

    def _block(self, row: int, col: int, color: tuple[int, int, int], filled: bool) -> None:
        pygame = self.pygame
        rect = pygame.Rect(BOARD_X + col * CELL + 2, BOARD_Y + row * CELL + 2, CELL - 4, CELL - 4)
        if filled:
            pygame.draw.rect(self.screen, color, rect, border_radius=4)
        else:
            pygame.draw.rect(self.screen, color, rect, 2, border_radius=4)

    def _draw_panel(self) -> None:
        pygame = self.pygame
        screen = self.screen
        session = self.session
        game = session.game
        panel = pygame.Rect(PANEL_X, BOARD_Y, PANEL_W - 8, ROWS * CELL)
        pygame.draw.rect(screen, PANEL, panel, border_radius=10)
        x = panel.x + 16
        right = panel.right - 16

        controls = (
            "Arrows   move",
            "Up       rotate",
            "Down     soft drop",
            "Space    hard drop",
            "A N H P  agents",
            "R        restart",
        )
        control_top = panel.bottom - 14
        for text in reversed(controls):
            image = self.small.render(text, True, MUTED)
            control_top -= image.get_height()
            screen.blit(image, (x, control_top))
            control_top -= 2
        control_top -= 8
        pygame.draw.line(screen, GRID, (x, control_top + 4), (right, control_top + 4))

        y = panel.top + 14

        def line(text: str, font, color, gap: int = 3) -> None:
            nonlocal y
            image = font.render(text, True, color)
            screen.blit(image, (x, y))
            y += image.get_height() + gap

        def stat(label: str, value: str, color=TEXT) -> None:
            nonlocal y
            label_image = self.small.render(label, True, MUTED)
            value_image = self.font.render(value, True, color)
            screen.blit(label_image, (x, y + 2))
            screen.blit(value_image, (x + 78, y))
            y += max(label_image.get_height(), value_image.get_height()) + 4

        line("TETRIS", self.bold, TEXT, 8)
        stat("Mode", MODE_LABELS[session.mode], ACCENT)
        stat("Score", f"{game.score:,}")
        stat("Lines", f"{game.lines:,}")
        stat("Pieces", f"{game.pieces:,}")
        stat("Piece", PIECE_NAMES[game.piece_id], PIECE_COLORS[game.piece_id])
        y += 6

        self._draw_decision(line, session.decision)

    def _draw_pose(self, line, decision) -> None:
        line("Decision", self.small, MUTED, 2)
        line(f"rot {decision.rotation}    col {decision.col}", self.font, TEXT, 1)

    def _draw_decision(self, line, decision) -> None:
        """What the side panel says about the current choice."""
        match self.session.mode:
            case "heuristic" if decision is not None:
                self._draw_pose(line, decision)
                line(f"{decision.candidates} legal drops", self.small, MUTED, 3)
                line(
                    f"L {decision.lines}   A {decision.aggregate_height}   "
                    f"holes {decision.holes}   B {decision.bumpiness}",
                    self.small,
                    TEXT,
                    2,
                )
                line(f"H  {decision.heuristic:.2f}", self.font, ACCENT, 1)
                line(
                    f"1.0*{decision.lines} - 0.5*{decision.aggregate_height} "
                    f"- 0.7*{decision.holes} - 0.3*{decision.bumpiness}",
                    self.small,
                    MUTED,
                    8,
                )
            case "height" if decision is not None:
                self._draw_pose(line, decision)
                line(f"minimize A = {decision.aggregate_height}", self.small, TEXT, 1)
                line(f"{decision.candidates} legal drops", self.small, MUTED, 8)
            case "random" if decision is not None:
                self._draw_pose(line, decision)
                line("uniform among legal drops", self.small, TEXT, 1)
                line(f"{decision.candidates} legal drops", self.small, MUTED, 8)
            case "human":
                line("You choose each move.", self.small, TEXT, 8)
            case _ if self.session.game.game_over:
                line("No legal drop.", self.small, GAME_OVER_COLOR, 8)

    def _draw_game_over(self) -> None:
        pygame = self.pygame
        overlay = pygame.Surface((COLS * CELL, ROWS * CELL), pygame.SRCALPHA)
        overlay.fill((8, 10, 20, 170))
        self.screen.blit(overlay, (BOARD_X, BOARD_Y))
        title = self.big.render("GAME OVER", True, GAME_OVER_COLOR)
        hint = self.font.render("R  restart", True, TEXT)
        center_x = BOARD_X + COLS * CELL // 2
        title_rect = title.get_rect(center=(center_x, BOARD_Y + ROWS * CELL // 2 - 16))
        hint_rect = hint.get_rect(center=(center_x, BOARD_Y + ROWS * CELL // 2 + 24))
        self.screen.blit(title, title_rect)
        self.screen.blit(hint, hint_rect)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    seed = args.seed if args.seed is not None else random.randrange(2**31)
    print(f"seed {seed}")
    session = Session(seed, ai=args.ai)
    try:
        App(session).run()
    except ModuleNotFoundError as exc:
        if exc.name in {"pygame", "pygame.ce"}:
            raise SystemExit(
                "The window needs pygame. Install it with: pip install pygame-ce"
            ) from exc
        raise
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
