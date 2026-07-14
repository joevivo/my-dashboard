from __future__ import annotations

import csv
from pathlib import Path
from typing import Iterable


HITTER_OVERLAY = Path("data/baseball/parsed/strat365/1968/draft-prep/1968.astrodome-hitter-recommendation-overlay-v0.csv")
STARTER_OVERLAY = Path("data/baseball/parsed/strat365/1968/draft-prep/1968.astrodome-starter-recommendation-overlay-v0.csv")
RELIEVER_OVERLAY = Path("data/baseball/parsed/strat365/1968/draft-prep/1968.astrodome-reliever-recommendation-overlay-v0.csv")

OUT_CSV = Path("data/baseball/parsed/strat365/1968/draft-prep/1968.astrodome-overlay-roster-scenarios-v0.csv")
OUT_MD = Path("data/baseball/parsed/strat365/1968/draft-prep/1968.astrodome-overlay-roster-scenarios-v0.md")


CAP = 80.0


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        raise FileNotFoundError(f"Missing required input: {path}")
    with path.open("r", newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def to_float(value: str) -> float:
    try:
        return float(value)
    except Exception:
        return 0.0


def to_int(value: str) -> int:
    try:
        return int(float(value))
    except Exception:
        return 0


def player_key(row: dict[str, str]) -> str:
    return row.get("playerId", "").strip()


def salary(row: dict[str, str]) -> float:
    return to_float(row.get("salary", ""))


def score(row: dict[str, str]) -> float:
    return to_float(row.get("astrodomeScore", ""))


def warnings(row: dict[str, str]) -> list[str]:
    value = row.get("warnings", "").strip()
    return [part for part in value.split(";") if part]


def label_player(row: dict[str, str]) -> str:
    return f"{row.get('playerName', '')} ({row.get('team', '')}, ${row.get('salary', '')})"


def add_player(
    roster: list[dict[str, str]],
    row: dict[str, str],
    role: str,
    seen: set[str],
) -> bool:
    key = player_key(row)
    if not key or key in seen:
        return False

    out = dict(row)
    out["rosterRole"] = role
    roster.append(out)
    seen.add(key)
    return True


def first_available(
    rows: Iterable[dict[str, str]],
    seen: set[str],
    predicate=lambda row: True,
) -> dict[str, str] | None:
    for row in rows:
        if player_key(row) in seen:
            continue
        if predicate(row):
            return row
    return None


def sort_high_score(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    return sorted(rows, key=lambda row: (-score(row), salary(row), row.get("playerName", "")))


def sort_value(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    return sorted(rows, key=lambda row: (-score(row), salary(row), row.get("playerName", "")))


def sort_salary_fit(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    return sorted(rows, key=lambda row: (salary(row), -score(row), row.get("playerName", "")))


def filter_recs(rows: list[dict[str, str]], recs: set[str]) -> list[dict[str, str]]:
    return [row for row in rows if row.get("recommendation") in recs]


def roster_salary(roster: list[dict[str, str]]) -> float:
    return round(sum(salary(row) for row in roster), 2)


def roster_warnings(roster: list[dict[str, str]]) -> list[str]:
    result: list[str] = []
    for row in roster:
        for warning in warnings(row):
            result.append(f"{row.get('playerName', '')}:{warning}")
    return result


def validate_roster(roster: list[dict[str, str]]) -> dict[str, str]:
    hitters = [row for row in roster if row.get("sourcePool") == "hitter"]
    pitchers = [row for row in roster if row.get("sourcePool") in {"starter", "reliever"}]

    total_salary = roster_salary(roster)
    primary_catchers = sum(1 for row in hitters if row.get("primaryPosition") == "C")
    starter_endurance = sum(1 for row in pitchers if to_int(row.get("starterEndurance", "0")) >= 5)
    pure_relievers = sum(
        1 for row in pitchers
        if row.get("sourcePool") == "reliever"
        and to_int(row.get("starterEndurance", "0")) == 0
        and to_int(row.get("reliefEndurance", "0")) > 0
    )
    closers = sum(1 for row in pitchers if to_int(row.get("closerEndurance", "0")) > 0)

    of_or_corner_bats_beyond_cf = sum(
        1 for row in hitters
        if row.get("rosterRole") != "clean_cf"
        and (
            row.get("positionGroup") == "Corner Bat"
            or row.get("primaryPosition") in {"LF", "RF", "1B"}
        )
    )
    primary_shortstops = sum(1 for row in hitters if row.get("primaryPosition") == "SS")
    middle_infield_types = sum(
        1 for row in hitters
        if row.get("primaryPosition") in {"SS", "2B"}
    )
    bench_bats = [
        row for row in hitters
        if row.get("rosterRole") in {"hitter_target", "salary_fit_hitter"}
    ]
    bench_bats_without_low_ob = sum(
        1 for row in bench_bats
        if "low_ob" not in warnings(row)
    )

    legal_checks = {
        "total_players": len(roster) == 25,
        "salary_cap": total_salary <= CAP,
        "hitters_13_to_17": 13 <= len(hitters) <= 17,
        "pitchers_11_to_14": 11 <= len(pitchers) <= 14,
        "primary_catchers_2_plus": primary_catchers >= 2,
        "starter_endurance_5_plus": starter_endurance >= 5,
        "pure_relievers_4_plus": pure_relievers >= 4,
        "closers_1_plus": closers >= 1,
    }

    credibility_checks = {
        "primary_catchers_3_or_less": primary_catchers <= 3,
        "salary_70_plus": total_salary >= 70.0,
        "warning_count_24_or_less": len(roster_warnings(roster)) <= 24,
        "of_corner_bats_beyond_cf_2_plus": of_or_corner_bats_beyond_cf >= 2,
        "primary_ss_3_or_less": primary_shortstops <= 3,
        "middle_infield_types_4_or_less": middle_infield_types <= 4,
        "bench_bat_without_low_ob_1_plus": bench_bats_without_low_ob >= 1,
    }

    legal = all(legal_checks.values())
    credible = legal and all(credibility_checks.values())

    return {
        "legal": "yes" if legal else "no",
        "credible": "yes" if credible else "no",
        "salary": f"{total_salary:.2f}",
        "players": str(len(roster)),
        "hitters": str(len(hitters)),
        "pitchers": str(len(pitchers)),
        "primaryCatchers": str(primary_catchers),
        "starterEndurancePitchers": str(starter_endurance),
        "pureRelievers": str(pure_relievers),
        "closers": str(closers),
        "ofCornerBatsBeyondCf": str(of_or_corner_bats_beyond_cf),
        "primaryShortstops": str(primary_shortstops),
        "middleInfieldTypes": str(middle_infield_types),
        "benchBatsWithoutLowOb": str(bench_bats_without_low_ob),
        "failedChecks": ";".join(key for key, passed in legal_checks.items() if not passed),
        "failedCredibilityChecks": ";".join(key for key, passed in credibility_checks.items() if not passed),
        "warningCount": str(len(roster_warnings(roster))),
    }


def decorate_sources(rows: list[dict[str, str]], source_pool: str) -> list[dict[str, str]]:
    out: list[dict[str, str]] = []
    for row in rows:
        copied = dict(row)
        copied["sourcePool"] = source_pool
        out.append(copied)
    return out


def build_scenario(
    name: str,
    hitters: list[dict[str, str]],
    starters: list[dict[str, str]],
    relievers: list[dict[str, str]],
    hitter_mode: str,
    starter_mode: str,
    reliever_mode: str,
) -> tuple[dict[str, str], list[dict[str, str]]]:
    hitter_core = filter_recs(hitters, {"core_target"})
    hitter_priority = filter_recs(hitters, {"position_priority"})
    hitter_useful = filter_recs(hitters, {"useful_value"})
    hitter_fallback = filter_recs(hitters, {"roster_structure_fallback"})

    starter_core = filter_recs(starters, {"core_target"})
    starter_useful = filter_recs(starters, {"useful_value"})
    starter_fallback = filter_recs(starters, {"roster_structure_fallback"})

    closer_targets = filter_recs(relievers, {"closer_target"})
    core_relievers = filter_recs(relievers, {"core_relief_target"})
    useful_closers = filter_recs(relievers, {"useful_closer_value"})
    useful_relievers = filter_recs(relievers, {"useful_relief_value"})
    reliever_fallback = filter_recs(relievers, {"roster_structure_fallback"})

    if hitter_mode == "premium":
        hitter_order = sort_high_score(hitter_core + hitter_priority + hitter_useful + hitter_fallback)
    elif hitter_mode == "position_first":
        hitter_order = sort_high_score(hitter_priority + hitter_core + hitter_useful + hitter_fallback)
    else:
        hitter_order = (
            sort_high_score(hitter_priority)
            + sort_high_score(hitter_useful)
            + sort_high_score(hitter_core)
            + sort_salary_fit(hitter_fallback)
        )

    if starter_mode == "premium":
        starter_order = sort_high_score(starter_core + starter_useful + starter_fallback)
    elif starter_mode == "value":
        starter_order = (
            sort_high_score(starter_useful)
            + sort_salary_fit(starter_fallback)
            + sort_high_score(starter_core)
        )
    else:
        starter_order = sort_high_score(starter_useful + starter_core + starter_fallback)

    if reliever_mode == "premium":
        reliever_order = sort_high_score(closer_targets + core_relievers + useful_closers + useful_relievers + reliever_fallback)
    else:
        reliever_order = (
            sort_high_score(closer_targets)
            + sort_high_score(core_relievers)
            + sort_high_score(useful_closers)
            + sort_high_score(useful_relievers)
            + sort_salary_fit(reliever_fallback)
        )

    roster: list[dict[str, str]] = []
    seen: set[str] = set()

    # Required hitter structure: 14 hitters.
    required_hitter_predicates = [
        ("primary_catcher", lambda row: row.get("primaryPosition") == "C"),
        ("primary_catcher", lambda row: row.get("primaryPosition") == "C"),
        ("clean_cf", lambda row: row.get("positionGroup") == "Clean CF"),
        ("clean_ss", lambda row: row.get("positionGroup") == "Clean SS"),
        ("clean_2b", lambda row: row.get("positionGroup") == "Clean 2B"),
        ("clean_3b", lambda row: row.get("positionGroup") == "Clean 3B"),
    ]

    for role, predicate in required_hitter_predicates:
        row = first_available(hitter_order, seen, predicate)
        if row:
            add_player(roster, row, role, seen)

    for row in hitter_order:
        if len([p for p in roster if p.get("sourcePool") == "hitter"]) >= 14:
            break

        current_hitters = [p for p in roster if p.get("sourcePool") == "hitter"]
        current_catchers = sum(1 for p in current_hitters if p.get("primaryPosition") == "C")
        current_shortstops = sum(1 for p in current_hitters if p.get("primaryPosition") == "SS")
        current_middle_infield = sum(1 for p in current_hitters if p.get("primaryPosition") in {"SS", "2B"})

        if row.get("primaryPosition") == "C" and current_catchers >= 3:
            continue
        if row.get("primaryPosition") == "SS" and current_shortstops >= 3:
            continue
        if row.get("primaryPosition") in {"SS", "2B"} and current_middle_infield >= 4:
            continue

        add_player(roster, row, "hitter_target", seen)

    # Required pitching structure: 5 starters + 6 pure relievers = 11 pitchers.
    for row in starter_order:
        if len([p for p in roster if p.get("sourcePool") == "starter"]) >= 5:
            break
        add_player(roster, row, "starter_target", seen)

    # Ensure at least one closer first.
    row = first_available(reliever_order, seen, lambda p: to_int(p.get("closerEndurance", "0")) > 0)
    if row:
        add_player(roster, row, "closer_target", seen)

    for row in reliever_order:
        if len([p for p in roster if p.get("sourcePool") == "reliever"]) >= 6:
            break
        add_player(roster, row, "relief_target", seen)

    # If over cap, conservatively replace expensive non-required hitters with cheap fallback hitters.
    def is_required_role(row: dict[str, str]) -> bool:
        return row.get("rosterRole") in {
            "primary_catcher",
            "clean_cf",
            "clean_ss",
            "clean_2b",
            "clean_3b",
            "starter_target",
            "closer_target",
        }

    fallback_order = (
        sort_salary_fit([row for row in hitter_useful if "low_ob" not in warnings(row)])
        + sort_salary_fit([row for row in hitter_fallback if "low_ob" not in warnings(row)])
        + sort_salary_fit(hitter_useful)
        + sort_salary_fit(hitter_fallback)
    )

    starter_salary_fit_order = (
        sort_salary_fit([row for row in starter_useful if len(warnings(row)) <= 1])
        + sort_salary_fit([row for row in starter_fallback if len(warnings(row)) <= 2])
        + sort_salary_fit(starter_useful)
        + sort_salary_fit(starter_fallback)
    )

    attempts = 0
    while roster_salary(roster) > CAP and attempts < 75:
        attempts += 1

        expensive_optional_hitters = [
            row for row in roster
            if row.get("sourcePool") == "hitter" and not is_required_role(row)
        ]

        expensive_starters = [
            row for row in roster
            if row.get("sourcePool") == "starter"
        ]

        remove_hitter = (
            sorted(expensive_optional_hitters, key=lambda row: salary(row), reverse=True)[0]
            if expensive_optional_hitters
            else None
        )
        remove_starter = (
            sorted(expensive_starters, key=lambda row: salary(row), reverse=True)[0]
            if expensive_starters
            else None
        )

        hitter_savings = salary(remove_hitter) if remove_hitter else 0.0
        starter_savings = salary(remove_starter) if remove_starter else 0.0

        if remove_starter and starter_savings >= hitter_savings:
            replacement = first_available(
                starter_salary_fit_order,
                seen,
                lambda row: (
                    salary(row) < salary(remove_starter)
                    and to_int(row.get("starterEndurance", "0")) >= 5
                ),
            )
            if replacement:
                roster.remove(remove_starter)
                seen.discard(player_key(remove_starter))
                add_player(roster, replacement, "salary_fit_starter", seen)
                continue

        if remove_hitter:
            current_hitters = [p for p in roster if p.get("sourcePool") == "hitter" and player_key(p) != player_key(remove_hitter)]
            current_catchers = sum(1 for p in current_hitters if p.get("primaryPosition") == "C")
            current_shortstops = sum(1 for p in current_hitters if p.get("primaryPosition") == "SS")
            current_middle_infield = sum(1 for p in current_hitters if p.get("primaryPosition") in {"SS", "2B"})

            replacement = first_available(
                fallback_order,
                seen,
                lambda row: (
                    salary(row) < salary(remove_hitter)
                    and not (row.get("primaryPosition") == "C" and current_catchers >= 3)
                    and not (row.get("primaryPosition") == "SS" and current_shortstops >= 3)
                    and not (row.get("primaryPosition") in {"SS", "2B"} and current_middle_infield >= 4)
                ),
            )
            if replacement:
                roster.remove(remove_hitter)
                seen.discard(player_key(remove_hitter))
                add_player(roster, replacement, "salary_fit_hitter", seen)
                continue

        break

    summary = validate_roster(roster)
    summary["scenario"] = name
    summary["hitterMode"] = hitter_mode
    summary["starterMode"] = starter_mode
    summary["relieverMode"] = reliever_mode

    return summary, roster


def write_csv(scenarios: list[tuple[dict[str, str], list[dict[str, str]]]]) -> None:
    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = [
        "scenario",
        "legal",
        "salary",
        "players",
        "hitters",
        "pitchers",
        "primaryCatchers",
        "starterEndurancePitchers",
        "pureRelievers",
        "closers",
        "warningCount",
        "failedChecks",
        "credible",
        "failedCredibilityChecks",
        "ofCornerBatsBeyondCf",
        "primaryShortstops",
        "middleInfieldTypes",
        "benchBatsWithoutLowOb",
        "hitterMode",
        "starterMode",
        "relieverMode",
    ]

    with OUT_CSV.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for summary, _ in scenarios:
            writer.writerow(summary)


def write_markdown(scenarios: list[tuple[dict[str, str], list[dict[str, str]]]]) -> None:
    lines: list[str] = [
        "# 1968 Astrodome Overlay Roster Scenarios",
        "",
        "These are card-backed roster-construction scenarios for human review. They are not autonomous draft picks.",
        "",
        "## Scenario Summary",
        "",
        "| Scenario | Legal | Credible | Salary | Players | Hitters | Pitchers | C | SP | Pure RP | Closers | OF/Corner | SS | MI | Bench no-low-OB | Warnings | Failed Checks | Failed Credibility Checks |",
        "|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|",
    ]

    for summary, _ in scenarios:
        lines.append(
            "| {scenario} | {legal} | {credible} | {salary} | {players} | {hitters} | {pitchers} | "
            "{primaryCatchers} | {starterEndurancePitchers} | {pureRelievers} | {closers} | "
            "{ofCornerBatsBeyondCf} | {primaryShortstops} | {middleInfieldTypes} | {benchBatsWithoutLowOb} | "
            "{warningCount} | {failedChecks} | {failedCredibilityChecks} |".format(**summary)
        )

    lines.append("")

    for summary, roster in scenarios:
        lines.append(f"## {summary['scenario']}")
        lines.append("")
        lines.append(
            f"Legal: {summary['legal']} | Credible: {summary['credible']} | Salary: ${summary['salary']} | "
            f"Warnings: {summary['warningCount']} | Failed checks: {summary['failedChecks'] or 'none'} | "
            f"Failed credibility checks: {summary['failedCredibilityChecks'] or 'none'}"
        )
        lines.append("")
        lines.append("| Role | Pool | Recommendation | Player | Salary | Position/Endurance | Warnings |")
        lines.append("|---|---|---|---|---:|---|---|")

        for row in roster:
            position_or_endurance = row.get("primaryPosition") or row.get("browserEndurance", "")
            lines.append(
                "| {role} | {pool} | {rec} | {player} | {salary} | {pos} | {warnings} |".format(
                    role=row.get("rosterRole", ""),
                    pool=row.get("sourcePool", ""),
                    rec=row.get("recommendation", ""),
                    player=label_player(row),
                    salary=row.get("salary", ""),
                    pos=position_or_endurance,
                    warnings=row.get("warnings", ""),
                )
            )

        lines.append("")

    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    hitters = decorate_sources(read_csv(HITTER_OVERLAY), "hitter")
    starters = decorate_sources(read_csv(STARTER_OVERLAY), "starter")
    relievers = decorate_sources(read_csv(RELIEVER_OVERLAY), "reliever")

    plans = [
        ("premium_sp_anchor", "value", "premium", "value"),
        ("balanced_card_score", "position_first", "balanced", "value"),
        ("premium_bats_value_pitching", "premium", "value", "value"),
        ("premium_pitching_and_relief", "value", "premium", "premium"),
    ]

    scenarios = [
        build_scenario(name, hitters, starters, relievers, hitter_mode, starter_mode, reliever_mode)
        for name, hitter_mode, starter_mode, reliever_mode in plans
    ]

    write_csv(scenarios)
    write_markdown(scenarios)

    print("# RESULT SUMMARY")
    print(f"CSV_OUT: {OUT_CSV}")
    print(f"MD_OUT: {OUT_MD}")
    for summary, _ in scenarios:
        print(
            f"{summary['scenario']}: legal={summary['legal']} credible={summary['credible']} "
            f"salary={summary['salary']} players={summary['players']} "
            f"hitters={summary['hitters']} pitchers={summary['pitchers']} "
            f"C={summary['primaryCatchers']} SP={summary['starterEndurancePitchers']} "
            f"RP={summary['pureRelievers']} CL={summary['closers']} "
            f"warnings={summary['warningCount']} failed={summary['failedChecks'] or 'none'} "
            f"credibility_failed={summary['failedCredibilityChecks'] or 'none'}"
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
