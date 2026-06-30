from __future__ import annotations

import argparse
import json
from pathlib import Path
from statistics import mean
from typing import Any


ROOT = Path(__file__).resolve().parents[2]

DEFAULT_PLAYERSET = ROOT / "data" / "baseball" / "parsed" / "strat365" / "1968" / "playerset" / "1968.playerset.json"
DEFAULT_BALLPARKS = ROOT / "data" / "baseball" / "parsed" / "strat365" / "1968" / "ballparks" / "1968.ballparks.json"
DEFAULT_OUT_DIR = ROOT / "data" / "baseball" / "parsed" / "strat365" / "1968" / "draft-signals"


def clamp(value: float, low: float = 0.0, high: float = 100.0) -> float:
    return max(low, min(high, value))


def score_payload(score: float) -> dict[str, float]:
    return {"score": round(clamp(score), 4)}


def salary_value_score(performance_score: float, salary_millions: float) -> float:
    # Browser-baseline value curve: cheap good players get rewarded, expensive players must earn the spend.
    return performance_score / max(0.65, salary_millions ** 0.58)


def range_defense_score(defense: str) -> float:
    # Browser field examples: 1(-2)e3, 3e25, 4(+4)e15.
    import re

    match = re.fullmatch(r"(?P<range>\d+)(?:\((?P<arm>[+-]?\d+)\))?e(?P<error>\d+)", defense or "")
    if not match:
        return 50.0

    range_rating = int(match.group("range"))
    error_rating = int(match.group("error"))
    arm_text = match.group("arm")

    range_score = {1: 98, 2: 84, 3: 66, 4: 43, 5: 25}.get(range_rating, 50)
    error_score = clamp(100 - (error_rating * 2.8))

    if arm_text is None:
        arm_score = 70
    else:
        arm = int(arm_text)
        # Negative OF/C arms are better; positive arms are worse.
        arm_score = clamp(70 - (arm * 6))

    return (range_score * 0.55) + (error_score * 0.30) + (arm_score * 0.15)


def running_score(run_rating: str, steal: str) -> float:
    try:
        high = int((run_rating or "1-10").split("-", 1)[1])
    except Exception:
        high = 10

    steal_score = {
        "AAA": 100,
        "AA": 94,
        "A": 88,
        "B": 76,
        "C": 62,
        "D": 48,
        "E": 36,
    }.get((steal or "").upper(), 50)

    return clamp(((high - 8) / 10) * 70 + steal_score * 0.30)


def hitter_performance_score(player: dict[str, Any]) -> float:
    obp = float(player.get("onBasePercentage") or 0)
    slg = float(player.get("sluggingPercentage") or 0)
    ab = max(1, int(player.get("ab") or 0))
    hr_rate = float(player.get("homeRuns") or 0) / ab
    bb_rate = float(player.get("walks") or 0) / max(1, ab + int(player.get("walks") or 0))

    obp_score = clamp((obp - 0.230) / 0.220 * 100)
    slg_score = clamp((slg - 0.250) / 0.360 * 100)
    hr_score = clamp(hr_rate / 0.065 * 100)
    walk_score = clamp(bb_rate / 0.180 * 100)

    return (
        obp_score * 0.44
        + slg_score * 0.31
        + hr_score * 0.13
        + walk_score * 0.12
    )


def pitcher_performance_score(player: dict[str, Any]) -> float:
    era = float(player.get("era") or 9.99)
    whip = float(player.get("whip") or 2.50)
    ip = innings_to_float(player.get("inningsPitched"))
    strikeouts = float(player.get("strikeouts") or 0)
    walks = float(player.get("walks") or 0)
    hr = float(player.get("homeRunsAllowed") or 0)

    era_score = clamp((5.20 - era) / 4.20 * 100)
    whip_score = clamp((1.75 - whip) / 0.95 * 100)
    k_per_9 = strikeouts * 9 / max(1.0, ip)
    bb_per_9 = walks * 9 / max(1.0, ip)
    hr_per_9 = hr * 9 / max(1.0, ip)

    k_score = clamp(k_per_9 / 10.5 * 100)
    control_score = clamp((5.0 - bb_per_9) / 4.0 * 100)
    hr_suppression_score = clamp((1.5 - hr_per_9) / 1.5 * 100)

    endurance = player.get("endurance") or ""
    endurance_bonus = 7 if "*" in endurance else 0
    if endurance.startswith("S9"):
        endurance_bonus += 5
    elif endurance.startswith("S8"):
        endurance_bonus += 3
    elif endurance.startswith("R"):
        endurance_bonus += 1

    return clamp(
        era_score * 0.34
        + whip_score * 0.29
        + k_score * 0.14
        + control_score * 0.11
        + hr_suppression_score * 0.12
        + endurance_bonus
    )


def innings_to_float(value: Any) -> float:
    text = str(value or "0")
    if "." not in text:
        return float(text)
    whole, partial = text.split(".", 1)
    outs = int(partial)
    return float(whole) + outs / 3


def park_shape_profile(ballpark: dict[str, Any]) -> dict[str, Any]:
    single_avg = float(ballpark["singleAverage"])
    homer_avg = float(ballpark["homerAverage"])

    return {
        "ballparkName": ballpark["name"],
        "singleAverage": single_avg,
        "homerAverage": homer_avg,
        "singleShape": ballpark["singleShape"],
        "homerShape": ballpark["homerShape"],
    }


def hitter_park_fit(player: dict[str, Any], park: dict[str, Any]) -> float:
    ab = max(1, int(player.get("ab") or 0))
    hr_rate = float(player.get("homeRuns") or 0) / ab
    singles_or_avg_dependency = float(player.get("battingAverage") or 0) - hr_rate

    power_fit = clamp((hr_rate / 0.065) * (float(park["homerAverage"]) - 10) * 2.2, -18, 18)
    single_fit = clamp((singles_or_avg_dependency / 0.300) * (float(park["singleAverage"]) - 10) * 1.2, -14, 14)

    return power_fit + single_fit


def pitcher_park_fit(player: dict[str, Any], park: dict[str, Any]) -> float:
    ip = innings_to_float(player.get("inningsPitched"))
    hr_per_9 = float(player.get("homeRunsAllowed") or 0) * 9 / max(1.0, ip)
    whip = float(player.get("whip") or 2.5)

    power_fit = clamp((1.2 - hr_per_9) * (10 - float(park["homerAverage"])) * 2.2, -18, 18)
    single_fit = clamp((1.35 - whip) * (10 - float(park["singleAverage"])) * 1.8, -14, 14)

    return power_fit + single_fit


def build_hitter_signal(player: dict[str, Any], ballparks: list[dict[str, Any]]) -> dict[str, Any]:
    performance = hitter_performance_score(player)
    defense = range_defense_score(player.get("defense") or "")
    running = running_score(player.get("runRating") or "", player.get("steal") or "")
    salary = float(player["salary"]["millions"])

    baseline = performance * 0.62 + defense * 0.20 + running * 0.08 + salary_value_score(performance, salary) * 0.10

    fits = []
    for park in ballparks:
        park_fit = hitter_park_fit(player, park)
        fits.append({
            **park_shape_profile(park),
            "browserParkFitScore": score_payload(50 + park_fit),
            "parkAdjustedBrowserScore": score_payload(baseline + park_fit * 0.28),
        })

    best_fit = max(fits, key=lambda item: item["parkAdjustedBrowserScore"]["score"])
    worst_fit = min(fits, key=lambda item: item["parkAdjustedBrowserScore"]["score"])

    return {
        "player": {
            "playerId": player["playerId"],
            "playerName": player["playerName"],
            "team": player["team"],
        },
        "role": "hitter",
        "rankable": True,
        "salary": player["salary"],
        "hitter": {
            "bats": player.get("bats"),
            "primaryPosition": player.get("primaryPosition"),
            "defense": player.get("defense"),
            "balance": player.get("balance"),
        },
        "browserPerformanceScore": score_payload(performance),
        "browserDefenseScore": score_payload(defense),
        "browserRunningScore": score_payload(running),
        "browserValueScore": score_payload(salary_value_score(performance, salary)),
        "browserBaselineDraftScore": score_payload(baseline),
        "ballparkProfile": {
            "bestFit": best_fit,
            "worstFit": worst_fit,
            "fitSpread": score_payload(best_fit["parkAdjustedBrowserScore"]["score"] - worst_fit["parkAdjustedBrowserScore"]["score"]),
        },
        "ballparkFits": fits,
    }


def build_pitcher_signal(player: dict[str, Any], ballparks: list[dict[str, Any]]) -> dict[str, Any]:
    performance = pitcher_performance_score(player)
    salary = float(player["salary"]["millions"])
    baseline = performance * 0.84 + salary_value_score(performance, salary) * 0.16

    fits = []
    for park in ballparks:
        park_fit = pitcher_park_fit(player, park)
        fits.append({
            **park_shape_profile(park),
            "browserParkFitScore": score_payload(50 + park_fit),
            "parkAdjustedBrowserScore": score_payload(baseline + park_fit * 0.30),
        })

    best_fit = max(fits, key=lambda item: item["parkAdjustedBrowserScore"]["score"])
    worst_fit = min(fits, key=lambda item: item["parkAdjustedBrowserScore"]["score"])

    return {
        "player": {
            "playerId": player["playerId"],
            "playerName": player["playerName"],
            "team": player["team"],
        },
        "role": "pitcher",
        "rankable": True,
        "salary": player["salary"],
        "pitcher": {
            "throws": player.get("throws"),
            "endurance": player.get("endurance"),
            "balance": player.get("balance"),
        },
        "browserPerformanceScore": score_payload(performance),
        "browserValueScore": score_payload(salary_value_score(performance, salary)),
        "browserBaselineDraftScore": score_payload(baseline),
        "ballparkProfile": {
            "bestFit": best_fit,
            "worstFit": worst_fit,
            "fitSpread": score_payload(best_fit["parkAdjustedBrowserScore"]["score"] - worst_fit["parkAdjustedBrowserScore"]["score"]),
        },
        "ballparkFits": fits,
    }


def assign_ranks(rows: list[dict[str, Any]], score_key: str, rank_key: str) -> None:
    rows.sort(key=lambda row: row[score_key]["score"], reverse=True)
    for index, row in enumerate(rows, start=1):
        row[rank_key] = index


def main() -> int:
    parser = argparse.ArgumentParser(description="Build browser-baseline draft signals for Strat365 1968.")
    parser.add_argument("--playerset", type=Path, default=DEFAULT_PLAYERSET)
    parser.add_argument("--ballparks", type=Path, default=DEFAULT_BALLPARKS)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    args = parser.parse_args()

    playerset = json.loads(args.playerset.read_text(encoding="utf-8"))
    ballpark_data = json.loads(args.ballparks.read_text(encoding="utf-8"))
    ballparks = ballpark_data["ballparks"]

    hitters = [build_hitter_signal(player, ballparks) for player in playerset["hitters"]]
    pitchers = [build_pitcher_signal(player, ballparks) for player in playerset["pitchers"]]

    assign_ranks(hitters, "browserBaselineDraftScore", "browserBaselineRank")
    assign_ranks(pitchers, "browserBaselineDraftScore", "browserBaselineRank")

    for rows in [hitters, pitchers]:
        for park in ballparks:
            park_name = park["name"]
            ranked = []
            for row in rows:
                fit = next(item for item in row["ballparkFits"] if item["ballparkName"] == park_name)
                ranked.append((fit["parkAdjustedBrowserScore"]["score"], row, fit))
            ranked.sort(key=lambda item: item[0], reverse=True)
            for index, (_, row, fit) in enumerate(ranked, start=1):
                fit["parkAdjustedBrowserRank"] = index

    payload = {
        "schemaVersion": "bie.browser-baseline-draft-signals.v0",
        "parserVersion": "parse_strat365_browser_baseline_draft_signals_v0",
        "season": int(playerset["season"]),
        "sourceFiles": {
            "playerset": str(args.playerset.relative_to(ROOT)).replace("\\", "/"),
            "ballparks": str(args.ballparks.relative_to(ROOT)).replace("\\", "/"),
        },
        "model": {
            "name": "browser-baseline-1968-v0",
            "principle": "Use public Strat365 browser stats, salary, primary-position defense, and ballpark factors only.",
            "limitations": [
                "Not card-probability based.",
                "Does not use authenticated player card split probabilities.",
                "Hitter defense is primary-position-only.",
                "Pitcher fielding defense is unavailable.",
                "Use as a first-pass draft triage layer, not final BIE ranking.",
            ],
        },
        "counts": {
            "ballparks": len(ballparks),
            "hitters": len(hitters),
            "pitchers": len(pitchers),
        },
        "hitters": hitters,
        "pitchers": pitchers,
    }

    args.out_dir.mkdir(parents=True, exist_ok=True)
    out_path = args.out_dir / "1968.browser-baseline-draft-signals.json"
    out_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    print("Wrote:", out_path)
    print("Hitters:", len(hitters))
    print("Pitchers:", len(pitchers))
    print()

    print("## Top 15 Browser-Baseline Hitters")
    for row in hitters[:15]:
        p = row["player"]
        print(
            f"- {row['browserBaselineRank']:>3}. {p['playerName']} | {p['team']} | "
            f"{row['hitter']['primaryPosition']} | {row['salary']['raw']} | "
            f"score {row['browserBaselineDraftScore']['score']:.2f} | "
            f"best park {row['ballparkProfile']['bestFit']['ballparkName']}"
        )

    print()
    print("## Top 15 Browser-Baseline Pitchers")
    for row in pitchers[:15]:
        p = row["player"]
        print(
            f"- {row['browserBaselineRank']:>3}. {p['playerName']} | {p['team']} | "
            f"{row['pitcher']['endurance']} | {row['salary']['raw']} | "
            f"score {row['browserBaselineDraftScore']['score']:.2f} | "
            f"best park {row['ballparkProfile']['bestFit']['ballparkName']}"
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
