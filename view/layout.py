"""Pixel layout and colors for the well and the side panel."""

from __future__ import annotations

from game.constants import COLS, ROWS

CELL = 32
PAD = 24
GAP = 28
PANEL_W = 320
BOARD_X = PAD
BOARD_Y = PAD
PANEL_X = BOARD_X + COLS * CELL + GAP
WIDTH = PANEL_X + PANEL_W + PAD
HEIGHT = BOARD_Y + ROWS * CELL + PAD

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
