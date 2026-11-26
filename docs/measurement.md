# Measurement

`evaluation/benchmark.py` plays the three policies on the same piece seeds and prints a report. It does not construct a `Game` or a `Session`, and it does not open a window. Survival is the number of pieces placed. A hard drop has no clock, so time-to-death is not a measure here.

Run it from the project root:

```bash
python -m evaluation.benchmark
```

`--seeds` defaults to 20, which is seeds 0 through 19. `--max-pieces` defaults to `MAX_PIECES` (10,000). Progress lines go to stderr, one per seed. The report goes to stdout.

## One headless game

`make_agent` builds a `RandomAgent(seed)`, a `HeightAgent`, or a `HeuristicAgent`. Anything else raises `ValueError`.

`play_game` keeps its own board, score, line total, and piece count. Its piece generator is `random.Random(seed)`, separate from `RandomAgent`'s generator. The loop is:

1. Draw a piece id.
2. Call `agent.select(board, piece_id)`.
3. Stop when that returns `None`.
4. `simulate_drop` the chosen rotation and column. Stop if that drop does not fit.
5. Replace the board with the copy, add the cleared lines, and add `line_score(cleared)`.
6. Stop after `max_pieces` successful locks.

`GameResult` records score, lines, pieces, and whether the loop stopped because of the cap. The window's heuristic death rule and this loop's death rule are the same event: `select` returned `None`. The human spawn rule is not part of the benchmark.

`run_benchmark` walks seeds from 0 and, within each seed, the order random, height-only, heuristic. Every policy therefore sees the same draws for that seed.

## The report

`format_report` prints six blocks:

1. The decision path: enumerate, drop from the top, copy and clear, score, break ties by enumeration order, stop on no legal drop or at the cap.
2. The weights, in the same words as `FORMULA`, plus what height-only and random do, and the separate 100/300/500/800 score table.
3. A summary table: average score, average lines, average pieces placed, and best pieces placed, for each policy.
4. Whether pieces placed ranked heuristic, then height-only, then random, and the heuristic's shortest and longest game. Games that hit the cap are named. When none do, the report says so.
5. Pieces placed on every seed.
6. Limits. The search is one ply, so it cannot prepare a well for an unseen next piece. Multi-ply search, Monte Carlo tree search, reinforcement learning, and a search over the weights are named as later work. The report also states the wall bias with a measured example: a height-4 stack in column 0 and the same stack in column 5. It states the tetris gap: the score table pays 800 for four lines at once, and `H` counts that the same as four ordinary lines (`L = 4`), which would score 400 if they were separate clears.

The wall-bias numbers are computed in the report by stacking four blocks and calling `measure`, so the printed `B` values come from the feature code rather than from a pasted constant.

## What the 20-seed run showed

No game hit the cap. Random never filled a row, so its score and line count are 0. On every seed, pieces placed ranked heuristic, then height-only, then random.

| Metric | Random | Height-only | Heuristic |
| --- | ---: | ---: | ---: |
| Average score | 0 | 1,785 | 31,215 |
| Average lines | 0.0 | 15.6 | 289.2 |
| Average pieces placed | 26.1 | 77.4 | 765.8 |
| Best pieces placed | 33 | 129 | 1,607 |

Heuristic games in that set run from 212 pieces to 1,607. Seed 4 is the short one, which is why `python main.py --ai --seed 4` is the demo and why restarting it repeats the same score. The policy is deterministic. A different seed is a different sequence and a different score. The table above is the measured output of this implementation. Re-run the module to print the full per-seed list.
