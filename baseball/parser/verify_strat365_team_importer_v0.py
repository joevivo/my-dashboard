from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from baseball.parser.import_strat365_team_roster_v0 import extract_metadata, parse_players


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> int:
    lines = [
        "TEAM: Imaginative Resistance",
        "Won the Championship in League: Auto League 475685",
        "Owner: imagination",
        "Manager: Daniel Altshuler",
        "Record: 90-72",
        "Home Ballpark: Astrodome 1980",
        "Initial Salary Cap: $80,000,000",
        "Total Current Value: $80,000,000",
        "Roster Value: $79,900,000",
        "Cash Available: $100,000",
        "Pitchers (3) min. 9, max. 12 (total min. 24, max. 28)",
        "Name T End. W L S BS IP H R ER BB SO HR Hold BkR WpR Bat ERA WHIP BAL Salary",
        "Reuss, J. L S7*/R3 23 12 0 0 306.1 309 115 101 45 130 27 -1 1 2 6NL 2.97 1.16 E 9.80M",
        "Bystrom, M. R S7/R3 14 10 0 0 214.1 180 82 71 66 100 11 -1 0 6 1WR 2.98 1.15 4L 6.98M",
        "Lacey, B. L R3 6 2 11 1 67.0 68 29 22 15 35 6 -4 0 14 1WR 2.96 1.24 7L 2.78M",
        "Hitters (3) min. 13, max. 17 (total min. 24, max. 28)",
        "Name B P Def. AB R H 2B 3B HR RBI BB SO HBP SB CS E Stl Run BA OBP SLG Inj BAL Salary",
        "Hassey, R. L C 3(+1)e4 460 60 139 15 5 5 66 68 79 1 0 0 4 E 1-9 .302 .389 .389 2 2R 5.40M",
        "Carew, R. L 1B 2e9 658 97 205 36 7 3 65 57 77 0 21 10 7 B 1-17 .312 .364 .401 1 1L 6.19M",
        "Geronimo, C. I-0 L CF 2(-3)e3 513 60 132 20 1 10 65 33 103 0 0 0 1 D 1-15 .257 .301 .359 1 E 2.50M",
        "TOTALS 90 72 35 4 1,458.2 1475 630 563 411 687 128 3.47 1.29",
    ]

    metadata = extract_metadata(lines, "https://365.strat-o-matic.com/team/1820660")
    players = parse_players(lines)

    require(metadata["team"] == "Imaginative Resistance", "team metadata mismatch")
    require(metadata["record"] == "90-72", "record metadata mismatch")
    require(metadata["ballpark"] == "Astrodome 1980", "ballpark metadata mismatch")
    require(metadata["rosterValue"] == "$79,900,000", "roster value metadata mismatch")

    require(len(players) == 6, f"expected 6 parsed players, found {len(players)}")

    by_name = {player.player_name: player for player in players}

    require(by_name["Reuss, J."].slot == "starter", "starter endurance was not classified as starter")
    require(by_name["Bystrom, M."].slot == "starter", "S7/R3 endurance was not classified as starter")
    require(by_name["Lacey, B."].slot == "relief", "R3 endurance was not classified as relief")
    require(by_name["Hassey, R."].slot == "C", "catcher position mismatch")
    require(by_name["Carew, R."].slot == "1B", "first base position mismatch")
    require(by_name["Geronimo, C."].slot == "CF", "injury-marker hitter row was not parsed correctly")

    print("PASS: Strat365 team importer smoke verification")
    print(f"Parsed players: {len(players)}")
    print(f"Team: {metadata['team']}")
    print(f"Ballpark: {metadata['ballpark']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
