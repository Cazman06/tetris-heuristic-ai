"""Keyboard, horizontal repeat, and the heuristic fall animation."""

from __future__ import annotations

from session import Session

DAS_DELAY = 180
DAS_REPEAT = 50
AI_TICK_MS = 16
AI_ROWS_PER_TICK = 3


class Controls:
    def __init__(self, pygame, session: Session) -> None:
        self.pygame = pygame
        self.session = session
        self.held: tuple[int, int, int] | None = None
        self.soft_held = False
        self.ai_ms = 0
        self.ai_hold = True
        self._modes = {pygame.K_a: "heuristic", pygame.K_p: "human"}
        self._steps = {pygame.K_LEFT: -1, pygame.K_RIGHT: 1}

    def stop(self) -> None:
        self.held = None
        self.soft_held = False
        self.ai_ms = 0
        self.ai_hold = True

    def key_down(self, key: int) -> bool:
        """Handle one key press. True when the play mode changed."""
        mode = self._modes.get(key)
        if mode is not None:
            if mode == self.session.mode:
                return False
            self.session.set_mode(mode)
            self.stop()
            return True
        pygame = self.pygame
        match key:
            case pygame.K_ESCAPE:
                pygame.event.post(pygame.event.Event(pygame.QUIT))
            case pygame.K_r:
                self.session.restart()
                self.stop()
            case pygame.K_LEFT | pygame.K_RIGHT | pygame.K_UP | pygame.K_DOWN | pygame.K_SPACE:
                self._human(key)
        return False

    def key_up(self, key: int) -> None:
        if self.held is not None and self.held[0] == key:
            self.held = None
        elif key == self.pygame.K_DOWN:
            self.soft_held = False

    def update(self, dt: int) -> None:
        if self.session.game.game_over:
            return
        if self.session.mode == "human":
            self._repeat(dt)
            self.session.tick_human(dt, soft=self.soft_held)
        else:
            self._animate(dt)

    def _human(self, key: int) -> None:
        session = self.session
        if session.mode != "human" or session.game.game_over:
            return
        pygame = self.pygame
        match key:
            case pygame.K_LEFT | pygame.K_RIGHT:
                step = self._steps[key]
                session.human_move(step)
                self.held = (key, step, 0)
            case pygame.K_UP:
                session.human_rotate()
            case pygame.K_DOWN:
                self.soft_held = True
                session.human_soft_drop()
            case pygame.K_SPACE:
                session.human_hard_drop()

    def _repeat(self, dt: int) -> None:
        if self.held is None:
            return
        key, step, held = self.held
        held += dt
        while held >= DAS_DELAY:
            self.session.human_move(step)
            held -= DAS_REPEAT
        self.held = (key, step, held)

    def _animate(self, dt: int) -> None:
        self.ai_ms += dt
        if self.ai_ms < AI_TICK_MS:
            return
        self.ai_ms = 0
        if self.ai_hold:
            self.ai_hold = False
            return
        for _ in range(AI_ROWS_PER_TICK):
            result = self.session.ai_fall_once()
            if result == "fall":
                continue
            self.ai_hold = result == "lock"
            return
