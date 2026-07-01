import argparse
import json
from pathlib import Path


def has_value(value):
    return value is not None and str(value).strip() != ""


def count_roster(players):
    hitters = [p for p in players if p.get("type") == "hitter"]
    pitchers = [p for p in players if p.get("type") == "pitcher"]

    primary_catchers = [
        p for p in hitters
        if str(p.get("primaryPosition", "")).upper() == "C"
    ]

    starting_endurance_pitchers = [
        p for p in pitchers
        if has_value(p.get("starterEndurance"))
    ]

    pure_relievers = [
        p for p in pitchers
        if has_value(p.get("reliefEndurance")) and not has_value(p.get("starterEndurance"))
    ]

    closer_endurance_pitchers = [
        p for p in pitchers
        if has_value(p.get("closerEndurance"))
    ]

    return {
        "players": len(players),
        "hitters": len(hitters),
        "pitchers": len(pitchers),
        "primaryCatchers": len(primary_catchers),
        "startingEndurancePitchers": len(starting_endurance_pitchers),
        "pureRelievers": len(pure_relievers),
        "closerEndurancePitchers": len(closer_endurance_pitchers),
    }


def check_min_max(violations, counts, key, min_key, max_key, rules, label):
    value = counts[key]
    min_value = rules.get(min_key)
    max_value = rules.get(max_key)

    if min_value is not None and value < min_value:
        violations.append({
            "code": f"{key}.belowMinimum",
            "message": f"{label}: {value} found; minimum is {min_value}."
        })

    if max_value is not None and value > max_value:
        violations.append({
            "code": f"{key}.aboveMaximum",
            "message": f"{label}: {value} found; maximum is {max_value}."
        })


def validate_roster(roster_doc, rules_doc):
    players = roster_doc.get("players", [])
    rules = rules_doc["roster"]
    counts = count_roster(players)
    violations = []

    check_min_max(violations, counts, "players", "minPlayers", "maxPlayers", rules, "Total players")
    check_min_max(violations, counts, "hitters", "minHitters", "maxHitters", rules, "Hitters")
    check_min_max(violations, counts, "pitchers", "minPitchers", "maxPitchers", rules, "Pitchers")

    minimum_checks = [
        ("primaryCatchers", "minPrimaryCatchers", "Primary catchers"),
        ("startingEndurancePitchers", "minStartingEndurancePitchers", "Pitchers with starter endurance"),
        ("pureRelievers", "minPureRelievers", "Pure relievers"),
        ("closerEndurancePitchers", "minCloserEndurancePitchers", "Pitchers with closer endurance"),
    ]

    for count_key, rule_key, label in minimum_checks:
        actual = counts[count_key]
        required = rules[rule_key]
        if actual < required:
            violations.append({
                "code": f"{count_key}.belowMinimum",
                "message": f"{label}: {actual} found; minimum is {required}."
            })

    return {
        "fixtureId": roster_doc.get("fixtureId"),
        "playerSet": roster_doc.get("playerSet"),
        "ruleSetId": rules_doc.get("ruleSetId"),
        "legal": len(violations) == 0,
        "counts": counts,
        "violations": violations,
    }


def main():
    parser = argparse.ArgumentParser(description="Validate a Strat365 Baseball roster fixture against a rules spec.")
    parser.add_argument("--rules", required=True, help="Path to roster rules JSON.")
    parser.add_argument("--roster", required=True, help="Path to roster fixture JSON.")
    args = parser.parse_args()

    rules_doc = json.loads(Path(args.rules).read_text(encoding="utf-8-sig"))
    roster_doc = json.loads(Path(args.roster).read_text(encoding="utf-8-sig"))

    result = validate_roster(roster_doc, rules_doc)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
