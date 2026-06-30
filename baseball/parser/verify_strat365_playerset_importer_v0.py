from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from baseball.parser.import_strat365_playerset_v0 import (
    HITTER_COLUMNS,
    PITCHER_COLUMNS,
    parse_hitter_row,
    parse_pitcher_row,
    parse_rows_from_html,
)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> int:
    hitter_html = """
    <html>
      <body>
        <table>
          <tr>
            <th>Name</th><th>Team</th><th>B</th><th>P</th><th>Def.</th><th>AB</th><th>R</th><th>H</th>
            <th>2B</th><th>3B</th><th>HR</th><th>RBI</th><th>BB</th><th>SO</th><th>SB</th><th>CS</th>
            <th>Stl</th><th>Run</th><th>BA</th><th>OBP</th><th>SLG</th><th>Inj</th><th>BAL</th><th>Salary</th>
          </tr>
          <tr>
            <td><a href="javascript:void(window.open('/player/43263/1968/5/1968'));">Yastrzemski, Carl</a></td>
            <td><a href="/playerset/browse/team/1968/15255">BOS '68</a></td>
            <td>L</td><td>LF</td><td>1(-3)e3</td><td>539</td><td>90</td><td>162</td>
            <td>32</td><td>2</td><td>23</td><td>74</td><td>119</td><td>90</td><td>13</td><td>6</td>
            <td>B</td><td>1-14</td><td>.301</td><td>.426</td><td>.495</td><td>1</td><td>2R</td><td>12.90M</td>
          </tr>
        </table>
      </body>
    </html>
    """

    pitcher_html = """
    <html>
      <body>
        <table>
          <tr>
            <th>Name</th><th>Team</th><th>T</th><th>End.</th><th>W</th><th>L</th><th>S</th>
            <th>IP</th><th>H</th><th>ER</th><th>BB</th><th>SO</th><th>HR</th><th>Hold</th>
            <th>BkR</th><th>WpR</th><th>Bat</th><th>ERA</th><th>WHIP</th><th>BAL</th><th>Salary</th>
          </tr>
          <tr>
            <td><a href="javascript:void(window.open('/player/31000/1968/5/1968'));">Gibson, Bob</a></td>
            <td><a href="/playerset/browse/team/1968/15261">STL '68</a></td>
            <td>R</td><td>S9*</td><td>22</td><td>9</td><td>0</td>
            <td>304.2</td><td>198</td><td>38</td><td>62</td><td>268</td><td>11</td><td>-3</td>
            <td>0</td><td>5</td><td>1WR</td><td>1.12</td><td>0.85</td><td>1R</td><td>9.03M</td>
          </tr>
        </table>
      </body>
    </html>
    """

    hitter_rows = parse_rows_from_html(hitter_html, HITTER_COLUMNS)
    pitcher_rows = parse_rows_from_html(pitcher_html, PITCHER_COLUMNS)

    require(len(hitter_rows) == 1, f"expected 1 hitter row, found {len(hitter_rows)}")
    require(len(pitcher_rows) == 1, f"expected 1 pitcher row, found {len(pitcher_rows)}")

    hitter = parse_hitter_row(hitter_rows[0], "1968", "10")
    pitcher = parse_pitcher_row(pitcher_rows[0], "1968", "1")

    require(hitter["role"] == "hitter", "hitter role mismatch")
    require(hitter["playerId"] == "43263", "hitter playerId mismatch")
    require(hitter["playerName"] == "Yastrzemski, Carl", "hitter name mismatch")
    require(hitter["teamId"] == "15255", "hitter teamId mismatch")
    require(hitter["primaryPosition"] == "LF", "hitter position mismatch")
    require(hitter["onBasePercentage"] == 0.426, "hitter OBP mismatch")
    require(hitter["salary"]["millions"] == 12.90, "hitter salary mismatch")

    require(pitcher["role"] == "pitcher", "pitcher role mismatch")
    require(pitcher["playerId"] == "31000", "pitcher playerId mismatch")
    require(pitcher["playerName"] == "Gibson, Bob", "pitcher name mismatch")
    require(pitcher["teamId"] == "15261", "pitcher teamId mismatch")
    require(pitcher["endurance"] == "S9*", "pitcher endurance mismatch")
    require(pitcher["era"] == 1.12, "pitcher ERA mismatch")
    require(pitcher["salary"]["millions"] == 9.03, "pitcher salary mismatch")

    print("PASS: Strat365 playerset importer smoke verification")
    print(f"Hitter: {hitter['playerName']} | {hitter['team']} | {hitter['salary']['raw']}")
    print(f"Pitcher: {pitcher['playerName']} | {pitcher['team']} | {pitcher['salary']['raw']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
