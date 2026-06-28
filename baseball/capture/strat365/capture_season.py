"""
BIE Product:
Capture v0.2
"""

import argparse
from datetime import datetime
import sys

from baseball.capture.strat365.discover_players import main as discover_players_main
from baseball.capture.strat365.capture_cards import capture_cards


BANNER = r"""
==========================================
      Baseball Intelligence Engine
          Capture v0.2
==========================================
"""


def main():
    parser = argparse.ArgumentParser(description="Capture a Strat365 season.")
    parser.add_argument("--season", required=True, type=int)
    parser.add_argument("--limit-cards", type=int, default=None)
    parser.add_argument("--skip-card-capture", action="store_true")
    args = parser.parse_args()

    start = datetime.now()

    print(BANNER)
    print(f"Season : {args.season}")
    print()

    print("STEP 1")
    print("Discover Players")
    print("----------------")

    original_argv = sys.argv
    try:
        sys.argv = ["discover_players", "--season", str(args.season)]
        discover_players_main()
    finally:
        sys.argv = original_argv

    if not args.skip_card_capture:
        print()
        print("STEP 2")
        print("Capture Cards")
        print("-------------")
        capture_cards(season=args.season, limit=args.limit_cards)

    elapsed = datetime.now() - start

    print()
    print("------------------------------------------")
    print("Capture pipeline complete.")
    print(f"Elapsed: {elapsed}")
    print("------------------------------------------")


if __name__ == "__main__":
    main()
