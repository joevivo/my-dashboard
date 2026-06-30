from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from baseball.parser.import_strat365_ballparks_v0 import classify_park, parse_ballparks


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> int:
    html = """
    <html>
      <body>
        <table>
          <tr>
            <th>Ballpark</th>
            <th>Capacity</th>
            <th>SI L</th>
            <th>SI R</th>
            <th>HR L</th>
            <th>HR R</th>
          </tr>
          <tr>
            <td>Astrodome 1968</td>
            <td>47,000</td>
            <td>9</td>
            <td>9</td>
            <td>1</td>
            <td>1</td>
          </tr>
          <tr>
            <td>Wrigley Field 1968</td>
            <td>36,755</td>
            <td>11</td>
            <td>19</td>
            <td>19</td>
            <td>19</td>
          </tr>
          <tr>
            <td>Busch Stadium 1968</td>
            <td>53,138</td>
            <td>1</td>
            <td>6</td>
            <td>1</td>
            <td>4</td>
          </tr>
        </table>
      </body>
    </html>
    """

    ballparks = parse_ballparks(html)

    require(len(ballparks) == 3, f"expected 3 ballparks, found {len(ballparks)}")

    by_name = {park.name: park for park in ballparks}

    require(by_name["Astrodome 1968"].capacity == 47000, "Astrodome capacity mismatch")
    require(by_name["Astrodome 1968"].si_left == 9, "Astrodome SI L mismatch")
    require(by_name["Astrodome 1968"].hr_right == 1, "Astrodome HR R mismatch")

    astrodome_shape = classify_park(by_name["Astrodome 1968"])
    require(astrodome_shape["homerShape"] == "power-suppressing", "Astrodome homer shape mismatch")

    wrigley_shape = classify_park(by_name["Wrigley Field 1968"])
    require(wrigley_shape["singleShape"] == "hit-amplifying", "Wrigley single shape mismatch")
    require(wrigley_shape["homerShape"] == "power-amplifying", "Wrigley homer shape mismatch")

    busch_shape = classify_park(by_name["Busch Stadium 1968"])
    require(busch_shape["singleShape"] == "hit-suppressing", "Busch single shape mismatch")
    require(busch_shape["homerShape"] == "power-suppressing", "Busch homer shape mismatch")

    print("PASS: Strat365 ballpark importer smoke verification")
    print(f"Parsed ballparks: {len(ballparks)}")
    print(f"Astrodome shape: {astrodome_shape['singleShape']} / {astrodome_shape['homerShape']}")
    print(f"Wrigley shape: {wrigley_shape['singleShape']} / {wrigley_shape['homerShape']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
