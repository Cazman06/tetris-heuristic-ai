"""The window loop. Windows owns maximize, minimize, and restore."""

from __future__ import annotations

import os

from session import MODE_LABELS, Session
from view.controls import Controls
from view.layout import HEIGHT, WIDTH
from view.paint import Fonts, draw


class App:
    def __init__(self, session: Session) -> None:
        os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
        import pygame

        self.pygame = pygame
        pygame.display.init()
        pygame.font.init()
        self.session = session
        self.minimized = False
        self.maximized = False
        self.window = pygame.Window("Tetris", (WIDTH, HEIGHT), resizable=True)
        screen = self.window.get_surface()
        self.canvas = pygame.Surface((WIDTH, HEIGHT)).convert(screen)
        self.clock = pygame.time.Clock()
        self.fonts = Fonts(pygame)
        self.controls = Controls(pygame, session)
        self._caption()

    def _caption(self) -> None:
        self.window.title = f"Tetris - {MODE_LABELS[self.session.mode]}"

    def run(self) -> None:
        running = True
        while running:
            dt = self.clock.tick(60)
            running = self._poll()
            if not running or self.minimized:
                continue
            self.controls.update(dt)
            draw(self.pygame, self.window, self.canvas, self.fonts, self.session)
            self.window.flip()
        self.pygame.quit()

    def _poll(self) -> bool:
        pygame = self.pygame
        running = True
        minimized = restored = maximized = False
        for event in pygame.event.get():
            match event.type:
                case pygame.QUIT:
                    running = False
                case pygame.WINDOWMINIMIZED:
                    minimized = True
                case pygame.WINDOWRESTORED:
                    restored = True
                case pygame.WINDOWMAXIMIZED:
                    maximized = True
                case pygame.KEYDOWN:
                    if self.controls.key_down(event.key):
                        self._caption()
                case pygame.KEYUP:
                    self.controls.key_up(event.key)
        self._apply_window(minimized, restored, maximized)
        return running

    def _apply_window(self, minimized: bool, restored: bool, maximized: bool) -> None:
        if minimized and not restored and not maximized:
            self.minimized = True
        elif maximized:
            self.minimized = False
            self.maximized = True
        elif restored:
            self.minimized = False
            self.maximized = False
