# Search

`ai/` decides a move without playing it. It copies the board, tries every legal hard drop of the current piece, and ranks the boards those drops leave behind. The package does not import Pygame. The window's heuristic and the benchmark's three policies all call `select(board, piece_id)` and get back a `Placement` or `None`.

| Module | Responsibility |
| --- | --- |
| `ai/simulate.py` | Copy, drop from the top, lock, clear |
| `ai/features.py` | Height, holes, bumpiness, and `H` |
| `ai/agents.py` | The placement record and the three policies |

## Simulated drops

`simulate_drop(board, piece_id, rotation, col)` calls `landing_row` starting at row 0. `None` from that call means the pose does not fit at the top, and the function returns `None`. Otherwise it copies the board, places the piece on the copy, clears lines, and returns `(new_board, lines_cleared)`. The caller's board is unchanged, including when the drop would clear rows.

`iter_drops` walks rotations from 0 upward, and for each rotation walks columns from 0 through `COLS - width`. It yields `(rotation, col, new_board, lines)` for every drop that fits. On an empty well that list is 17 moves for I, 9 for O, 34 for T, 17 for S, 17 for Z, 34 for J, and 34 for L. A nearly full well yields fewer, and a board with no legal pose yields nothing.

## Features

After a drop, `measure` reads the cleared board and returns three integers: aggregate height `A`, `holes`, and bumpiness `B`. Lines cleared, `L`, come from the simulator, because the cleared rows are already gone when the other three are measured.

Column height is the distance from the floor to the highest block in that column. An empty column is 0. A hole under a block still counts toward height: the height is the top of the stack, not the number of filled cells. A hole is an empty cell with at least one block above it in the same column. Bumpiness is the sum of absolute height differences between neighboring columns, nine gaps across ten columns.

The published evaluation is

```text
H(s) = 1.0*L - 0.5*A - 0.7*holes - 0.3*B
```

A clear is the only positive term. Per unit, a hole is the strongest penalty, then a unit of height, then a unit of roughness. The weights are constants in `ai/features.py`. They were chosen, not searched for.

Ranking uses the integer `10*H`, computed as `10*L - 5*A - 7*holes - 3*B`. Multiplying through avoids comparing `0.7` and `0.3` as floats, so two boards with the same integer rank are genuine ties. `published_h` is the float form, and the panel prints it. It is not what `pick_best` compares.

Bumpiness treats a stack against the wall as smoother than the same stack in the middle, because a wall has only one neighbor. A column of height 4 in column 0 has `B = 4`. The same column in column 5 has `B = 8`. An opening O on seed 4 therefore goes in column 0.

## Placements

`Placement` is a frozen record: rotation, column, lines cleared, aggregate height, holes, bumpiness, and `candidates`. `heuristic` on the record is `published_h` of those features, for display.

`all_placements` runs `iter_drops`, measures each resulting board, and builds one record per legal drop. `candidates` is filled in a second pass so every record carries the size of the list. An empty list stays empty. That empty list is how a policy reports that the piece cannot be placed.

`pick_best` walks the list once. It keeps a candidate only when its rank is strictly greater than the best rank so far. Equal ranks leave the earlier record in place, and the earlier record is the earlier rotation, then the left-er column, because that is the order `iter_drops` produces.

## The three policies

`HeuristicAgent.select` ranks with `heuristic_value`. `HeightAgent.select` ranks with `-A`, so it only tries to keep the stack short. A line clear helps that policy when the clear lowers the sum of heights, and the policy ignores holes and bumpiness otherwise. `RandomAgent.select` draws uniformly from the same list. It owns a `Random(seed)` that `reset` rebuilds. That generator is not the piece generator.

All three return `None` when `all_placements` is empty. The benchmark treats that as the end of the game. The window only constructs `HeuristicAgent`. Height-only and random stay available for measurement.

The search does not prune, and it does not look at the following piece. Every legal drop of the current piece is scored, the winner is played, and the next decision starts from the board that lock produced.
