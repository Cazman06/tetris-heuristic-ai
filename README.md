# Tetris heuristic

A playable Tetris game with a one-step heuristic on top of it. The game and the agent meet at one contract, so each half can be built and tested alone.

The board is 20 rows by 10 columns. Row 0 is the top. `0` is empty, and `1`–`7` are the seven tetrominoes (I, O, T, S, Z, J, L). A move is a rotation and a leftmost column. The piece hard-drops from the top of that column. There are no wall kicks.

Simulation copies the board, drops, locks, clears lines, and returns the new board plus the number of lines cleared. The live game is unchanged until that move is played.

## Run it locally

Use Python 3.13 or newer, from the project root. `pygame-ce` supplies the `pygame` module the window imports.

```bash
python -m pip install -r requirements.txt
python main.py                  # human
python main.py --ai --seed 4    # watch the heuristic
python -m evaluation.benchmark  # 20 shared seeds
pytest
```

`--seed` fixes the piece sequence. Omit it and the window picks a seed and prints it. `R` restarts that same seed. The benchmark flag `--seeds` defaults to 20 (seeds 0–19) and `--max-pieces` defaults to 10,000.

On this machine `python` may be the Microsoft Store alias. `py -3.15 main.py` is the same command against the installed interpreter.

## Window

The window is a grid and a side panel. There is no next-piece box, hold, sound, or menu.

| Key | Action |
| --- | --- |
| Left / Right | Move |
| Up | Rotate clockwise |
| Down | Soft drop |
| Space | Hard drop |
| A | Heuristic mode |
| P | Human mode |
| R | Restart the same piece seed |
| Esc | Quit |

The panel calls these modes. Human pieces lock about half a second after they land, so you can still slide. The heuristic hard-drops. A human dies when the spawn pose overlaps the stack. The heuristic dies when the current piece has no legal drop, which can still be true after the center columns are blocked.

While the heuristic plays, the panel shows the chosen rotation and column, how many legal drops were scored, and the features of the board that drop leaves behind.

## Decision

Each piece is drawn independently and uniformly. The agent does not see the next piece.

1. Enumerate every rotation and every leftmost column.
2. Hard-drop that pose from the top. A pose that overlaps a block or leaves the well is discarded.
3. Copy the board, lock the piece, and clear full rows.
4. Score the result. `L` is the number of rows removed. Height, holes, and bumpiness are measured after the clear, because those rows are gone.
5. Play the highest score. An equal score keeps the earliest rotation, then the leftmost column.
6. Spawn the next piece. Stop when no legal drop remains, or after 10,000 pieces.

The evaluation function is

```text
H(s) = 1.0*L - 0.5*A - 0.7*holes - 0.3*B
```

| Term | Meaning |
| --- | --- |
| L | Lines cleared by this drop |
| A | Sum of column heights. Height is the distance from the bottom to the highest block. Empty columns are 0. |
| holes | Empty cells with a block above them in the same column |
| B | Sum of absolute height gaps between neighboring columns |

A clear is the reward. Per unit, holes are the strongest penalty, then height, then roughness. These weights were not fit by a search. Ranking uses `10*H` in integers, so the weights compare exactly.

Height-only minimizes `A` and ignores `L`, holes, and `B`. Random chooses uniformly among the legal drops, with its own random stream, so it does not disturb the shared piece seed.

The game score is separate from `H`: 100, 300, 500, and 800 for one to four lines.

## 20 shared seeds

Seeds 0–19. Same piece sequence for every agent. Pieces placed is survival, because a hard drop has no real-time clock. No game hit the 10,000-piece cap. Random scored 0 because it never filled a row before the stack reached the top.

| Metric | Random | Height-only | Heuristic |
| --- | ---: | ---: | ---: |
| Average score | 0 | 1,785 | 31,215 |
| Average lines | 0.0 | 15.6 | 289.2 |
| Average pieces placed | 26.1 | 77.4 | 765.8 |
| Best pieces placed | 33 | 129 | 1,607 |

On every seed, pieces placed rank heuristic, then height-only, then random. Heuristic survival runs from 212 to 1,607 pieces. `python -m evaluation.benchmark` reprints the decision path, the weights, this table, the per-seed counts, and the limits below.

## Limits

This is one ply. The next piece is unknown, so the search cannot set up a well for it. Multi-ply search, Monte Carlo tree search, reinforcement learning, and a search over these weights stay later.

Bumpiness treats a stack against the wall as smoother than the same stack in the center. A height-4 stack in column 0 has `B = 4`. The same stack in column 5 has `B = 8`. That is why an opening O on seed 4 goes in column 0.

The score table pays extra for a four-line clear (800) that `H` counts as four ordinary lines. Four separate one-line clears score 400 and also have `L = 4`.

## Layout

| Path | Role |
| --- | --- |
| `game/` | Rules only. No Pygame and no agent imports. |
| `ai/` | Simulated drops, legal moves, features, and the three agents. |
| `session.py` | Live play: human lock delay, and agents applied to the current piece. |
| `main.py` | The window. |
| `evaluation/benchmark.py` | Headless paired measurement. |
| `tests/` | Rules, the search, and agreement between the engine and the benchmark. |
