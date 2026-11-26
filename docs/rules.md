# Rules

`game/` is the Tetris rules and nothing else. It does not import Pygame, and it does not import `ai/`. Rendering and policy both sit on top of this package.

| Module | Responsibility |
| --- | --- |
| `game/constants.py` | Well size, the empty cell, the score table, the 10,000-piece cap |
| `game/pieces.py` | Shape tables and the piece draw |
| `game/board.py` | Locked cells: fit, fall, place, clear |
| `game/engine.py` | One live game: spawn, move, rotate, drop, lock, score |

## The well

`COLS` is 10 and `ROWS` is 20. `EMPTY` is 0. A board is a list of 20 rows, each a list of 10 ints. `empty_board` builds one. `copy_board` copies every row so a simulation can lock a piece without touching the original.

`MAX_PIECES` is 10,000. The window does not stop at that number. The benchmark does, because a hard drop has no real-time clock and pieces placed is the survival measure.

## Pieces

Ids are fixed: I=1, O=2, T=3, S=4, Z=5, J=6, L=7. `SHAPES[0]` is empty so a cell value can be used as an index. `PIECE_NAMES` maps those ids to letters for the panel.

Each rotation is a tuple of `(row, col)` offsets. The shapes are stored already normalized: the smallest row is 0 and the smallest column is 0. Column 0 of a shape is its leftmost block, which is what "leftmost column" means for a move. Rotations go clockwise. Counts are 2 for I, 1 for O, 4 for T, J, and L, and 2 for S and Z. O never changes. I, S, and Z each have a flat pose and a tall pose.

`cells(piece_id, rotation, row, col)` adds the pose origin to every offset. That origin is the top-left of the shape's bounding box, not necessarily a filled cell. The flat T, for example, has an empty cell at `(0, 0)`.

`piece_width` is one more than the largest column offset, so the search knows how far right that rotation can sit: columns `0` through `COLS - width`.

`draw_piece` returns `1 + rng.randrange(7)`. The same `Random` instance, reseeded from the game seed in `Game.reset`, produces the same sequence every time.

## Fitting, landing, locking, clearing

`fits` is true when every cell of the pose is inside the well and the board cell is empty. A negative row or column fails. There is no kick: the caller asks about one pose, and a no is final.

`landing_row` starts at a given row (0 for a search drop, the current row for a live hard drop). If the pose does not fit there, it returns `None`. Otherwise it walks down one row at a time and stops at the last row that fits. The piece does not pass through blocks.

`place` writes the piece id into those cells. It assumes the pose fits. `clear_lines` keeps rows that still contain an empty cell, counts how many rows were dropped, and prepends that many empty rows so survivors shift toward the floor. It returns the count and mutates the board it was given.

## The live engine

`Game(seed)` owns the piece generator, the locked board, the score, the line count, the piece count, and the current pose. `reset` rebuilds the generator from the same seed and spawns the first piece. `game_over` exists on the object, and this module never sets it. `session.py` decides death, because a human and the heuristic use different tests.

Spawn draws a piece, sets rotation to 0, and centers it using the width of that rotation: `col = (COLS - width) // 2`, `row = 0`.

`move(dc)` shifts the column by one when the new pose fits. `rotate` advances the rotation index and keeps the origin where it is. Overlap with the stack or the wall leaves the old rotation in place.

`soft_drop` moves down one row, or locks if the next row is blocked. It returns `"fall"`, `"lock"`, or `"idle"`. Locking here is immediate. Human lock delay is implemented above this, in the session, by waiting before it calls a drop.

`hard_drop` asks `landing_row` from the current row, moves there, and locks. It returns `"idle"` when the current pose does not fit.

`_lock` places the piece, clears lines, adds `line_score(cleared)` to the score, increments `lines` and `pieces`, and spawns the next piece. A lock that clears nothing adds 0.

`ghost_cells` is the outline the window draws. It is the same landing computation, and it returns nothing when the piece is already on the floor or does not fit. The ghost is not a move and it is not written to the board.
