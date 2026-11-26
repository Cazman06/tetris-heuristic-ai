"""Play Tetris, or watch the one-ply heuristic.

    python main.py                 # human
    python main.py --ai --seed 4   # watch the heuristic
"""

from __future__ import annotations

import argparse
import random

from session import Session
from view.app import App


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Play Tetris, or watch a one-ply heuristic.")
    parser.add_argument("--ai", action="store_true", help="start under the heuristic agent")
    parser.add_argument("--seed", type=int, default=None, help="piece-sequence seed")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    seed = args.seed if args.seed is not None else random.randrange(2**31)
    print(f"seed {seed}")
    try:
        App(Session(seed, ai=args.ai)).run()
    except ModuleNotFoundError as exc:
        if exc.name in {"pygame", "pygame.ce"}:
            raise SystemExit(
                "The window needs pygame. Install it with: pip install pygame-ce"
            ) from exc
        raise
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
