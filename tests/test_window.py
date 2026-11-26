"""Maximize and minimize stay on the window Windows already created."""

from __future__ import annotations

import os

import pytest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

from session import Session
from main import HEIGHT, WIDTH, App


@pytest.fixture
def app():
    window = App(Session(0))
    yield window
    window.pygame.quit()


def test_window_starts_at_the_layout_size(app):
    assert app.fullscreen is False
    assert app.minimized is False
    assert app.window.size == (WIDTH, HEIGHT)


def test_maximize_does_not_switch_video_mode(app):
    pygame = app.pygame
    pygame.event.post(pygame.event.Event(pygame.WINDOWMAXIMIZED))
    assert app._poll()
    assert app.fullscreen is True
    assert app.minimized is False
    assert app.window.size == (WIDTH, HEIGHT)


def test_minimize_after_maximize_stays_minimized(app):
    pygame = app.pygame
    pygame.event.post(pygame.event.Event(pygame.WINDOWMAXIMIZED))
    app._poll()
    pygame.event.post(pygame.event.Event(pygame.WINDOWMINIMIZED))
    assert app._poll()
    assert app.minimized is True
    assert app.fullscreen is True
    assert app.window.size == (WIDTH, HEIGHT)
    assert app._poll()
    assert app.minimized is True


def test_restore_from_taskbar_keeps_the_maximized_window(app):
    pygame = app.pygame
    pygame.event.post(pygame.event.Event(pygame.WINDOWMAXIMIZED))
    app._poll()
    pygame.event.post(pygame.event.Event(pygame.WINDOWMINIMIZED))
    app._poll()
    pygame.event.post(pygame.event.Event(pygame.WINDOWRESTORED))
    pygame.event.post(pygame.event.Event(pygame.WINDOWMAXIMIZED))
    app._poll()
    assert app.minimized is False
    assert app.fullscreen is True


def test_restore_down_returns_to_the_layout_size(app):
    pygame = app.pygame
    pygame.event.post(pygame.event.Event(pygame.WINDOWMAXIMIZED))
    app._poll()
    pygame.event.post(pygame.event.Event(pygame.WINDOWRESTORED))
    app._poll()
    assert app.fullscreen is False
    assert app.minimized is False
    assert app.window.size == (WIDTH, HEIGHT)
