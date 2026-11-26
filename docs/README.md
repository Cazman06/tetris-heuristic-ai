# How the code works

This folder explains the program from the outside in. Each page stays at the level of modules, data, and the path a piece takes. The root [README](../README.md) covers how to run it and what the measured games look like.

| Page | What it covers |
| --- | --- |
| [Overview](overview.md) | The shared contract, and the two ways a game is played |
| [Rules](rules.md) | `game/`: the well, the pieces, collision, clears, and the live engine |
| [Search](search.md) | `ai/`: simulated drops, the four features, and the three policies |
| [Play](play.md) | `session.py` and `view/`: modes, timing, and the window |
| [Measurement](measurement.md) | `evaluation/benchmark.py`: paired seeds and the printed report |
| [Tests](tests.md) | What `tests/` locks in |

The packages are separated on purpose. `game/` imports neither Pygame nor `ai/`. The search reads boards through simulation and never touches the window. The benchmark does not run the window either. `session.py` is the only place that applies a policy to a live game.
