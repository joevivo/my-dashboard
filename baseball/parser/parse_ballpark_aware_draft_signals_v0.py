import json
from datetime import datetime, timezone
from pathlib import Path

SEASON = 1980
PARSER_VERSION = "ballpark_aware_draft_signals_v0"

BALLPARKS_FILE = Path("data/baseball/parsed/strat365/1980/ballparks/ballparks_v0.json")
DEFENSE_AWARE_FILE = Path("data/baseball/parsed/strat365/1980/draft-signals/1980.defense-aware-draft-signals.json")
PROFILE_FILE = Path("data/baseball/parsed/strat365/1980/matchup-player-profiles/1980.matchup-player-profiles.json")
CARD_SUMMARY_DIR = Path("data/baseball/parsed/strat365/1980/card-probability-summaries")

OUT_DIR = Path("data/baseball/parsed/strat365/1980/draft-signals")
OUT_FILE = OUT_DIR / "1980.ballpark-aware-draft-signals.json"

NEUTRAL_FACTOR = 10.0
MAX_FACTOR = 20.0
PARK_FIT_BONUS_WEIGHT = 0.25


def dec(obj, default=0.0):
    if isinstance(obj, dict):
        value = obj.get("decimal")
        return float(value) if value is not None else default
    return default


def score_obj(value):
    value = round(float(value), 4)
    return {"score": value}


def defense_score(row):
    score = row.get("defenseAwareDraftScore", {}).get("score")
    return float(score) if score is not None else 0.0


def park_adjusted_score(row, fit_score):
    # fitScore is centered around 50. Only the park delta is added.
    # This preserves the core defense-aware model while surfacing park-specific movement.
    return defense_score(row) + ((float(fit_score) - 50.0) * PARK_FIT_BONUS_WEIGHT)


def park_bucket(park):
    si_avg = (park["singleFactorLeft"] + park["singleFactorRight"]) / 2
    hr_avg = (park["homeRunFactorLeft"] + park["homeRunFactorRight"]) / 2

    if si_avg >= 14 and hr_avg >= 14:
        return "run_amplifier"
    if si_avg <= 6 and hr_avg <= 6:
        return "run_suppressor"
    if hr_avg >= 14:
        return "power_amplifier"
    if hr_avg <= 6:
        return "power_suppressor"
    if si_avg >= 14:
        return "singles_amplifier"
    if si_avg <= 6:
        return "singles_suppressor"
    return "neutral_mixed"


def side_hand(side):
    if side == "vs_left_pitcher":
        return "L"
    if side == "vs_right_pitcher":
        return "R"
    return None


def load_card_ballpark_dependencies(player_id):
    path = CARD_SUMMARY_DIR / f"{player_id}.card-probability-summary.json"
    if not path.exists():
        return []

    data = json.loads(path.read_text(encoding="utf-8"))
    rows = []

    for side in data.get("sides", []):
        deps = side.get("dependencyWeights", {})
        base = side.get("baseOutcomeWeights", {})
        rows.append({
            "side": side.get("side"),
            "pitcherHand": side_hand(side.get("side")),
            "ballparkHomeRunCheckWeight": dec(deps.get("ballpark_home_run_check")),
            "ballparkSingleCheckWeight": dec(deps.get("ballpark_single_check")),
            "baseHomeRunWeight": dec(base.get("HOME_RUN")),
            "baseSingleWeight": dec(base.get("SINGLE")),
        })

    return rows


def avg(values):
    values = [v for v in values if v is not None]
    return sum(values) / len(values) if values else 0.0


def factor_delta(factor):
    return (float(factor) - NEUTRAL_FACTOR) / MAX_FACTOR


def factor_conversion(factor):
    return float(factor) / MAX_FACTOR


def hitter_park_fit(player, parks):
    player_id = player["player"]["playerId"]
    deps = load_card_ballpark_dependencies(player_id)

    hr_check = avg([x["ballparkHomeRunCheckWeight"] for x in deps])
    si_check = avg([x["ballparkSingleCheckWeight"] for x in deps])
    base_hr = avg([x["baseHomeRunWeight"] for x in deps])
    base_si = avg([x["baseSingleWeight"] for x in deps])

    fits = []
    for park in parks:
        hr_factor = avg([park["homeRunFactorLeft"], park["homeRunFactorRight"]])
        si_factor = avg([park["singleFactorLeft"], park["singleFactorRight"]])

        hr_delta = hr_check * factor_delta(hr_factor)
        si_delta = si_check * factor_delta(si_factor)

        # Hitter value rises when parks convert more HR/SI checks.
        ballpark_fit_score = 50 + (hr_delta * 900) + (si_delta * 450) + (base_hr * factor_delta(hr_factor) * 120)

        fits.append({
            "ballparkId": park["ballparkId"],
            "ballparkName": park["ballparkName"],
            "bucket": park_bucket(park),
            "factors": {
                "singleLeft": park["singleFactorLeft"],
                "singleRight": park["singleFactorRight"],
                "homeRunLeft": park["homeRunFactorLeft"],
                "homeRunRight": park["homeRunFactorRight"],
            },
            "ballparkImpact": {
                "homeRunCheckWeight": round(hr_check, 6),
                "singleCheckWeight": round(si_check, 6),
                "baseHomeRunWeight": round(base_hr, 6),
                "baseSingleWeight": round(base_si, 6),
                "homeRunDelta": round(hr_delta, 6),
                "singleDelta": round(si_delta, 6),
                "fitScore": score_obj(ballpark_fit_score),
                "parkAdjustedDraftScore": score_obj(park_adjusted_score(player, ballpark_fit_score)),
            },
        })

    best = max(fits, key=lambda x: x["ballparkImpact"]["fitScore"]["score"])
    worst = min(fits, key=lambda x: x["ballparkImpact"]["fitScore"]["score"])

    return {
        "player": player["player"],
        "role": "hitter",
        "rankable": player.get("rankable", False),
        "defenseAwareRank": player.get("defenseAwareRank"),
        "defenseAwareDraftScore": player.get("defenseAwareDraftScore"),
        "hitter": player.get("hitter"),
        "salary": player.get("salary"),
        "ballparkProfile": {
            "homeRunCheckWeight": round(hr_check, 6),
            "singleCheckWeight": round(si_check, 6),
            "baseHomeRunWeight": round(base_hr, 6),
            "baseSingleWeight": round(base_si, 6),
            "bestFit": best,
            "worstFit": worst,
            "fitSpread": score_obj(best["ballparkImpact"]["fitScore"]["score"] - worst["ballparkImpact"]["fitScore"]["score"]),
        },
        "ballparkFits": fits,
    }


def pitcher_park_fit(player, pitcher_profile, parks):
    outcomes = pitcher_profile.get("outcomeAverages", {}) if pitcher_profile else {}

    allowed_hr = dec(outcomes.get("HOME_RUN"))
    allowed_si = dec(outcomes.get("SINGLE"))
    allowed_fb = dec(outcomes.get("FLYBALL"))
    allowed_gb = dec(outcomes.get("GROUNDBALL"))

    fits = []
    for park in parks:
        hr_factor = avg([park["homeRunFactorLeft"], park["homeRunFactorRight"]])
        si_factor = avg([park["singleFactorLeft"], park["singleFactorRight"]])

        hr_exposure_delta = allowed_hr * factor_delta(hr_factor)
        si_exposure_delta = allowed_si * factor_delta(si_factor)

        # Pitcher value rises when parks suppress exposed HR/SI outcomes.
        ballpark_fit_score = 50 - (hr_exposure_delta * 1100) - (si_exposure_delta * 350) - (allowed_fb * factor_delta(hr_factor) * 70)

        fits.append({
            "ballparkId": park["ballparkId"],
            "ballparkName": park["ballparkName"],
            "bucket": park_bucket(park),
            "factors": {
                "singleLeft": park["singleFactorLeft"],
                "singleRight": park["singleFactorRight"],
                "homeRunLeft": park["homeRunFactorLeft"],
                "homeRunRight": park["homeRunFactorRight"],
            },
            "ballparkImpact": {
                "allowedHomeRunWeight": round(allowed_hr, 6),
                "allowedSingleWeight": round(allowed_si, 6),
                "allowedFlyballWeight": round(allowed_fb, 6),
                "allowedGroundballWeight": round(allowed_gb, 6),
                "homeRunExposureDelta": round(hr_exposure_delta, 6),
                "singleExposureDelta": round(si_exposure_delta, 6),
                "fitScore": score_obj(ballpark_fit_score),
                "parkAdjustedDraftScore": score_obj(park_adjusted_score(player, ballpark_fit_score)),
            },
        })

    best = max(fits, key=lambda x: x["ballparkImpact"]["fitScore"]["score"])
    worst = min(fits, key=lambda x: x["ballparkImpact"]["fitScore"]["score"])

    return {
        "player": player["player"],
        "role": "pitcher",
        "rankable": player.get("rankable", False),
        "defenseAwareRank": player.get("defenseAwareRank"),
        "defenseAwareDraftScore": player.get("defenseAwareDraftScore"),
        "pitcher": player.get("pitcher"),
        "salary": player.get("salary"),
        "ballparkProfile": {
            "allowedHomeRunWeight": round(allowed_hr, 6),
            "allowedSingleWeight": round(allowed_si, 6),
            "allowedFlyballWeight": round(allowed_fb, 6),
            "allowedGroundballWeight": round(allowed_gb, 6),
            "bestFit": best,
            "worstFit": worst,
            "fitSpread": score_obj(best["ballparkImpact"]["fitScore"]["score"] - worst["ballparkImpact"]["fitScore"]["score"]),
        },
        "ballparkFits": fits,
    }



def add_park_specific_ranks(rows):
    by_park = {}
    for row in rows:
        for fit in row.get("ballparkFits", []):
            by_park.setdefault(fit["ballparkName"], []).append((row, fit))

    for park_name, items in by_park.items():
        items.sort(
            key=lambda item: (
                -item[1]["ballparkImpact"]["parkAdjustedDraftScore"]["score"],
                item[0]["player"]["playerName"],
            )
        )
        for rank_number, (row, fit) in enumerate(items, start=1):
            fit["ballparkImpact"]["parkAdjustedRank"] = rank_number


def rank(rows):
    rankable = [r for r in rows if r.get("rankable")]
    rankable.sort(key=lambda r: (
        -r["defenseAwareDraftScore"]["score"],
        -r["ballparkProfile"]["fitSpread"]["score"],
        r["player"]["playerName"],
    ))
    for i, row in enumerate(rankable, start=1):
        row["ballparkAwareRank"] = i


def main():
    ballparks_data = json.loads(BALLPARKS_FILE.read_text(encoding="utf-8"))
    defense_data = json.loads(DEFENSE_AWARE_FILE.read_text(encoding="utf-8"))
    profiles_data = json.loads(PROFILE_FILE.read_text(encoding="utf-8"))

    parks = ballparks_data["ballparks"]

    pitcher_profiles_by_id = {
        row["player"]["playerId"]: row
        for row in profiles_data.get("pitcherProfiles", [])
    }

    hitters = [hitter_park_fit(row, parks) for row in defense_data["hitters"]]
    pitchers = [
        pitcher_park_fit(row, pitcher_profiles_by_id.get(row["player"]["playerId"]), parks)
        for row in defense_data["pitchers"]
    ]

    rank(hitters)
    rank(pitchers)
    add_park_specific_ranks(hitters)
    add_park_specific_ranks(pitchers)

    payload = {
        "schemaVersion": 1,
        "parserVersion": PARSER_VERSION,
        "season": SEASON,
        "sourceFiles": {
            "ballparks": str(BALLPARKS_FILE),
            "defenseAwareDraftSignals": str(DEFENSE_AWARE_FILE),
            "matchupPlayerProfiles": str(PROFILE_FILE),
            "cardProbabilitySummaries": str(CARD_SUMMARY_DIR),
        },
        "model": {
            "name": "ballpark-aware draft signal v0",
            "principle": "Separate ballpark-context layer; does not modify deterministic card evidence.",
            "neutralFactor": NEUTRAL_FACTOR,
            "maxFactor": MAX_FACTOR,
            "parkFitBonusWeight": PARK_FIT_BONUS_WEIGHT,
            "hitterFit": "Rewards hitter card ballpark HR/SI check opportunity in parks with high HR/SI factors.",
            "pitcherFit": "Rewards pitcher profiles in parks that suppress allowed HR/SI exposure.",
            "limitations": [
                "Uses average L/R park factors in v0.",
                "Does not yet use projected league handedness mix.",
                "Does not yet model specific roster construction or platoon deployment.",
            ],
        },
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "counts": {
            "ballparks": len(parks),
            "hitters": len(hitters),
            "pitchers": len(pitchers),
        },
        "hitters": hitters,
        "pitchers": pitchers,
    }

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_FILE.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    print(f"Saved {OUT_FILE}")
    print(f"Hitters: {len(hitters)}")
    print(f"Pitchers: {len(pitchers)}")
    print()
    print("Top hitter fit spreads:")
    for row in sorted(hitters, key=lambda r: r["ballparkProfile"]["fitSpread"]["score"], reverse=True)[:10]:
        print(
            f"- {row['player']['playerName']}: spread {row['ballparkProfile']['fitSpread']['score']} | "
            f"best {row['ballparkProfile']['bestFit']['ballparkName']} | "
            f"worst {row['ballparkProfile']['worstFit']['ballparkName']}"
        )
    print()
    print("Top pitcher fit spreads:")
    for row in sorted(pitchers, key=lambda r: r["ballparkProfile"]["fitSpread"]["score"], reverse=True)[:10]:
        print(
            f"- {row['player']['playerName']}: spread {row['ballparkProfile']['fitSpread']['score']} | "
            f"best {row['ballparkProfile']['bestFit']['ballparkName']} | "
            f"worst {row['ballparkProfile']['worstFit']['ballparkName']}"
        )


if __name__ == "__main__":
    main()
