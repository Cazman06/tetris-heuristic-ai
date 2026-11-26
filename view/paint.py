"""Draw the well, the side panel, and scale the frame to the window."""

from __future__ import annotations

from game.constants import COLS, ROWS
from game.pieces import PIECE_NAMES
from session import MODE_LABELS, Session
from view.layout import (
    ACCENT,
    BG,
    BOARD_X,
    BOARD_Y,
    BORDER,
    CELL,
    GAME_OVER_COLOR,
    GRID,
    HEIGHT,
    MUTED,
    PANEL,
    PANEL_W,
    PANEL_X,
    PIECE_COLORS,
    TEXT,
    WELL,
    WIDTH,
)

PLAY_KEYS = (
    ("Arrows", "move"),
    ("Up", "rotate"),
    ("Down", "soft drop"),
    ("Space", "hard drop"),
    ("R", "restart"),
)
MODE_KEYS = (
    ("A", "heuristic"),
    ("P", "human"),
)


class Fonts:
    def __init__(self, pygame) -> None:
        sysfont = pygame.font.SysFont
        self.text = sysfont("segoeui", 18)
        self.small = sysfont("segoeui", 16)
        self.bold = sysfont("segoeui", 22, bold=True)
        self.big = sysfont("segoeui", 36, bold=True)


def draw(pygame, window, canvas, fonts: Fonts, session: Session) -> None:
    canvas.fill(BG)
    _well(pygame, canvas, session)
    _panel(pygame, canvas, fonts, session)
    if session.game.game_over:
        _game_over(pygame, canvas, fonts)
    _present(pygame, window, canvas)


def _present(pygame, window, canvas) -> None:
    """Blit the layout onto the window. A larger window scales it to fit."""
    screen = window.get_surface()
    sw, sh = screen.get_size()
    if (sw, sh) == (WIDTH, HEIGHT):
        screen.blit(canvas, (0, 0))
        return
    scale = min(sw / WIDTH, sh / HEIGHT)
    size = (max(1, round(WIDTH * scale)), max(1, round(HEIGHT * scale)))
    scaled = pygame.transform.smoothscale(canvas, size)
    screen.fill(BG)
    screen.blit(scaled, ((sw - size[0]) // 2, (sh - size[1]) // 2))


def _block(pygame, screen, row: int, col: int, color: tuple[int, int, int], filled: bool) -> None:
    rect = pygame.Rect(BOARD_X + col * CELL + 2, BOARD_Y + row * CELL + 2, CELL - 4, CELL - 4)
    if filled:
        pygame.draw.rect(screen, color, rect, border_radius=4)
    else:
        pygame.draw.rect(screen, color, rect, 2, border_radius=4)


def _well(pygame, screen, session: Session) -> None:
    game = session.game
    board = pygame.Rect(BOARD_X, BOARD_Y, COLS * CELL, ROWS * CELL)
    pygame.draw.rect(screen, WELL, board)
    for col in range(COLS + 1):
        x = BOARD_X + col * CELL
        pygame.draw.line(screen, GRID, (x, board.top), (x, board.bottom))
    for row in range(ROWS + 1):
        y = BOARD_Y + row * CELL
        pygame.draw.line(screen, GRID, (board.left, y), (board.right, y))
    pygame.draw.rect(screen, BORDER, board, 2)

    for row in range(ROWS):
        for col in range(COLS):
            piece_id = game.board[row][col]
            if piece_id:
                _block(pygame, screen, row, col, PIECE_COLORS[piece_id], filled=True)

    if not game.current_fits():
        return
    color = PIECE_COLORS[game.piece_id]
    for row, col in game.ghost_cells():
        _block(pygame, screen, row, col, color, filled=False)
    for row, col in game.current_cells():
        _block(pygame, screen, row, col, color, filled=True)


def _panel(pygame, screen, fonts: Fonts, session: Session) -> None:
    game = session.game
    panel = pygame.Rect(PANEL_X, BOARD_Y, PANEL_W - 8, ROWS * CELL)
    pygame.draw.rect(screen, PANEL, panel, border_radius=10)
    x = panel.x + 16
    right = panel.right - 16
    y = _keys(screen, fonts.small, x, panel.bottom - 14) - 8
    pygame.draw.line(screen, GRID, (x, y + 4), (right, y + 4))
    y = panel.top + 14

    def line(text: str, font, color, gap: int = 3) -> None:
        nonlocal y
        image = font.render(text, True, color)
        screen.blit(image, (x, y))
        y += image.get_height() + gap

    def stat(label: str, value: str, color=TEXT) -> None:
        nonlocal y
        label_image = fonts.small.render(label, True, MUTED)
        value_image = fonts.text.render(value, True, color)
        screen.blit(label_image, (x, y + 2))
        screen.blit(value_image, (x + 78, y))
        y += max(label_image.get_height(), value_image.get_height()) + 4

    line("TETRIS", fonts.bold, TEXT, 8)
    stat("Mode", MODE_LABELS[session.mode], ACCENT)
    stat("Score", f"{game.score:,}")
    stat("Lines", f"{game.lines:,}")
    stat("Pieces", f"{game.pieces:,}")
    stat("Piece", PIECE_NAMES[game.piece_id], PIECE_COLORS[game.piece_id])
    y += 6
    _decision(line, fonts, session)


def _keys(screen, small, x: int, bottom: int) -> int:
    """Draw the key list from the bottom. Keys share one column; actions start on the next."""
    labels = [key for key, _action in (*PLAY_KEYS, *MODE_KEYS)]
    action_x = x + max(small.size(key)[0] for key in labels) + 20
    y = bottom

    def row(key: str, action: str) -> None:
        nonlocal y
        key_image = small.render(key, True, MUTED)
        action_image = small.render(action, True, TEXT)
        y -= max(key_image.get_height(), action_image.get_height())
        screen.blit(key_image, (action_x - 20 - key_image.get_width(), y))
        screen.blit(action_image, (action_x, y))
        y -= 3

    def rows(pairs: tuple[tuple[str, str], ...]) -> None:
        for key, action in reversed(pairs):
            row(key, action)

    rows(MODE_KEYS)
    heading = small.render("Modes", True, MUTED)
    y -= heading.get_height()
    screen.blit(heading, (x, y))
    y -= 8
    rows(PLAY_KEYS)
    return y


def _decision(line, fonts: Fonts, session: Session) -> None:
    decision = session.decision
    if session.mode == "heuristic" and decision is not None:
        line("Decision", fonts.small, MUTED, 2)
        line(f"rot {decision.rotation}    col {decision.col}", fonts.text, TEXT, 1)
        line(f"{decision.candidates} legal drops", fonts.small, MUTED, 3)
        line(
            f"L {decision.lines}   A {decision.aggregate_height}   "
            f"holes {decision.holes}   B {decision.bumpiness}",
            fonts.small,
            TEXT,
            2,
        )
        line(f"H  {decision.heuristic:.2f}", fonts.text, ACCENT, 1)
        line(
            f"1.0*{decision.lines} - 0.5*{decision.aggregate_height} "
            f"- 0.7*{decision.holes} - 0.3*{decision.bumpiness}",
            fonts.small,
            MUTED,
            8,
        )
        return
    if session.mode == "human":
        line("You choose each move.", fonts.small, TEXT, 8)
    elif session.game.game_over:
        line("No legal drop.", fonts.small, GAME_OVER_COLOR, 8)


def _game_over(pygame, screen, fonts: Fonts) -> None:
    overlay = pygame.Surface((COLS * CELL, ROWS * CELL), pygame.SRCALPHA)
    overlay.fill((*WELL, 170))
    screen.blit(overlay, (BOARD_X, BOARD_Y))
    title = fonts.big.render("GAME OVER", True, GAME_OVER_COLOR)
    hint = fonts.text.render("R  restart", True, TEXT)
    center_x = BOARD_X + COLS * CELL // 2
    center_y = BOARD_Y + ROWS * CELL // 2
    screen.blit(title, title.get_rect(center=(center_x, center_y - 16)))
    screen.blit(hint, hint.get_rect(center=(center_x, center_y + 24)))
