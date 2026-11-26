# Tests

`pytest.ini` puts the project root on `pythonpath` and collects `tests/`. From the project root, `pytest` runs both modules. They check the rules, the search, and that the live engine and the benchmark agree. They do not open a window.

## `tests/test_rules.py`

This file locks the game package.

Shapes must match the stored rotations, including the normalization where each shape's minimum row and column are 0. Rotation counts are part of that check. Piece ids are 1 through 7 in the order I, O, T, S, Z, J, L.

`draw_piece` on a seeded generator is deterministic, and across many draws it hits each id. The score table is 100, 300, 500, and 800, and any other line count scores 0.

Line clears drop full rows, keep partial rows in order, and shift survivors down by prepending empty rows. A board with no full row is left alone. `fits` rejects a pose that leaves the well or overlaps a filled cell.

The engine, reset twice from the same seed, produces the same piece sequence. Move and rotate succeed when the destination fits and leave the pose alone when it does not. Single, double, and four-line clears add the matching scores. A soft drop to the floor and a hard drop from the same start lock the same cells and the same score.

A final test reads the `game` sources and asserts they do not import `pygame` or `ai`.

## `tests/test_agents.py`

This file locks the search and the session rules that differ by mode.

The weights are 1.0, 0.5, 0.7, and 0.3, and the integer rank is 10, 5, 7, and 3 times those terms. One hole ranks worse than one unit of height, which ranks worse than one unit of bumpiness. A hand-built board checks height, a buried hole, and the wall-versus-center bumpiness gap.

`simulate_drop` must not mutate the board it is given, and it must clear a row when the drop fills one. Empty-well move counts are 17, 9, 34, 17, 17, 34, and 34 for I through L. A board whose every cell is filled makes all three policies return `None`.

On a board one I away from a clear, both the heuristic and the height-only policy take that clear. `pick_best` keeps the earlier record when ranks are equal. Two `RandomAgent`s built with the same seed pick the same opening move.

`play_game` and a `Game` driven with the same decisions stay in agreement for random, height-only, and heuristic on seeds 0–2, up to 40 pieces. A five-piece cap marks the game as capped. A report built from fixed results includes the formula, `B = 4` and `B = 8`, the 800-point tetris line, and the one-ply limit. `run_benchmark(seeds=1, max_pieces=15)` runs and reports a capped heuristic game.

Session tests cover the death split: a blocked center spawn ends a human game, and the heuristic on that board still places the piece off to the side. Human lock delay waits `LOCK_MS` before the piece locks, and `ai_fall_once` locks on contact. Restarting a heuristic game replays the board and the pose. Sources under `ai/`, `evaluation/`, and `session.py` are checked so they do not mention Pygame.

Window drawing and keyboard layout are not covered here. Those are checked by running `main.py`.
