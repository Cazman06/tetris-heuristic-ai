# Play

Live play is `session.py` plus `view/`. The session owns the rules object and the mode. `view/app.py` owns the frame loop, `view/controls.py` owns the keyboard and the heuristic animation, and `view/paint.py` owns the drawing. `main.py` parses the arguments and starts those. Pygame is imported inside `App.__init__`, so importing `session` or `game` does not require it. The process sets `SDL_AUDIODRIVER` to `dummy` and never opens the mixer. There is no sound.

## Modes

`MODES` is `("human", "heuristic")`. The panel calls them modes. `A` selects the heuristic and `P` selects human. Starting with `--ai` begins in heuristic mode. Otherwise the window starts in human mode.

`Session` holds one `Game` and one `HeuristicAgent`. `set_mode` rejects anything outside those two names, and it does nothing when the mode is already selected. A real change stores the mode and calls `prepare`, which re-reads the piece that is already on screen.

`restart` resets the game from the same seed and calls `prepare` again. The piece sequence starts over. The mode stays.

## What prepare does

`prepare` runs after every spawn, after a restart, and after a mode change. It clears the lock timer and the gravity timer.

If the game is already over, it clears the stored decision and returns.

In human mode there is no agent. The decision is cleared. If the current pose does not fit, the session sets `game_over`. After a normal spawn that pose is the centered piece at row 0, which is the human death test: the middle of the top row is blocked.

In heuristic mode, `select` runs on the locked board and the current piece id. `None` means no legal drop, and the session ends the game. Otherwise it stores the `Placement` and moves the live piece to rotation `decision.rotation`, column `decision.col`, row 0. If that pose does not fit, the game ends as well. Drops returned by the search already fit at row 0, so this is the same condition checked again on the live board.

Changing mode mid-piece is allowed. Switching to the heuristic snaps the current piece back to row 0 in the column the search just chose. Switching to human leaves the piece where it is and hands the controls over, unless that pose overlaps the stack.

## Human timing

These clocks belong to the session and the window. The benchmark never uses them.

| Constant | Value | Role |
| --- | --- | --- |
| `GRAVITY_MS` | 800 | Time between automatic one-row drops |
| `SOFT_MS` | 40 | The same interval while Down is held |
| `LOCK_MS` | 500 | Time a landed piece can still be slid |
| `DAS_DELAY` | 180 | Hold time before Left or Right repeats |
| `DAS_REPEAT` | 50 | Interval of that repeat |

`tick_human` accumulates milliseconds. While the piece can still fall, crossing the gravity interval calls `_descend`, which steps the row down. When the next row is blocked, `_descend` starts `lock_ms` at 0 instead of locking. Further ticks add to `lock_ms`, and at 500 ms `_commit_lock` calls `Game.hard_drop`.

A successful move or rotation calls `_after_shift`. If the piece can fall again, the lock timer is cleared, so sliding off a ledge resumes gravity. If it is still on the floor, the lock timer restarts at 0, which gives another half second after the slide.

Down, on the key press, drops one row immediately through `human_soft_drop`. Holding Down only changes the interval `tick_human` uses. Space calls `_commit_lock` at once, from whatever row the piece is on.

Human methods return immediately unless the mode is human and the game is still running. Arrow keys during heuristic play do not move the piece.

## Heuristic timing

The search result is applied in `prepare`, at row 0. The window then animates the fall. It does not call `hard_drop` for the heuristic.

Every frame, `Controls` adds the frame time. Every `AI_TICK_MS` (16 ms) it may move the piece. `ai_hold` spends one of those ticks doing nothing after a lock, so the newly chosen pose is visible at the top before it starts falling. Then each tick calls `ai_fall_once` up to `AI_ROWS_PER_TICK` (3) times.

`ai_fall_once` calls `Game.soft_drop`. That steps one row, or locks immediately on contact, with no lock delay. On `"lock"`, the session runs `prepare` for the next piece and the window sets `ai_hold` again. Because the column and rotation were chosen up front and never change during the fall, the animated path is the hard drop the search scored.

## The window

`main` parses `--ai` and `--seed`. A missing seed becomes `random.randrange(2**31)`, and the seed is printed. `Session` is built, then `App.run` loops at 60 frames: events, update, draw.

The window is a well and a side panel. Cell size is 32 pixels, with padding and a 320-pixel panel. There is no next box, hold box, or menu. It opens at that layout size. Maximize, minimize, and restore are the window's own buttons. Windows chooses the maximized size for the monitor the window is on, and the board is drawn at the layout size, then scaled to fit that window and centered. The same background fills any margin. While the window is minimized the game loop waits instead of drawing.

Keyboard handling is a lookup plus `match` in `view/controls.py`:

- `A` and `P` map onto the two mode names.
- Left and Right map onto a column step. The held state is `(key, step, held_ms)`. Releasing one direction does not cancel the other.
- Escape posts a quit event. `R` restarts. The remaining keys are human controls, and they return at once unless the mode is human.

The well draws locked cells, then the ghost outline, then the falling piece, using `PIECE_COLORS`. The ghost and the piece are skipped when the current pose does not fit, which is the game-over case.

The panel shows mode, score, lines, pieces, and the current piece letter. Under that, heuristic mode prints the chosen rotation and column, how many legal drops were scored, `L`, `A`, holes, `B`, the float `H`, and the arithmetic that produced it. Human mode prints "You choose each move." Game over draws a veil on the well and "GAME OVER", with `R` as the restart hint. The control list is pinned to the bottom of the panel in two columns: keys on the right of their column, actions on the left of the next. The word "Modes" labels `A` and `P`.

If `pygame` cannot be imported, `main` exits with a message to install `pygame-ce`. That package provides the `pygame` module.
