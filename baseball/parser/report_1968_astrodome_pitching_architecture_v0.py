from __future__ import annotations

import csv
import json
import re
from itertools import combinations
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]

FIXTURE_PATH = (
    ROOT
    / "data/baseball/fixtures/rosters/"
    / "1968_astrodome_alou_freehan_chance_parker_v0.json"
)
MECHANICS_PATH = (
    ROOT
    / "data/baseball/parsed/strat365/1968/card-mechanics/"
    / "1968.pitcher-card-mechanics-v0.csv"
)
METADATA_PATH = (
    ROOT
    / "data/baseball/parsed/strat365/1968/player-roster-metadata/"
    / "1968.player-roster-metadata.json"
)
CARD_ROOT = (
    ROOT
    / "data/baseball/parsed/strat365/1968/"
    / "card-probability-summaries"
)
OUTPUT_JSON = (
    ROOT
    / "data/baseball/parsed/strat365/1968/reports/"
    / "1968.astrodome-pitching-architecture-v0.json"
)
OUTPUT_MD = (
    ROOT
    / "data/baseball/parsed/strat365/1968/reports/"
    / "1968.astrodome-pitching-architecture-v0.md"
)

CAP_MILLIONS = 80.0

ROTATION = [
    "Chance, Dean",
    "Niekro, Phil",
    "Washburn, Ray",
    "Singer, Bill",
]

CURRENT_SWINGMAN = "Moose, Bob"
PRIMARY_ALTERNATIVE_SWINGMAN = "Jackson, Al"

FINALISTS = [
    "Moose, Bob",
    "Jackson, Al",
    "Osteen, Claude",
    "Hunter, Catfish",
]

START_ARCHITECTURES = {
    "four_man_starred": {
        "Chance, Dean": 41,
        "Niekro, Phil": 41,
        "Washburn, Ray": 40,
        "Singer, Bill": 40,
        "Moose, Bob": 0,
    },
    "five_man": {
        "Chance, Dean": 33,
        "Niekro, Phil": 33,
        "Washburn, Ray": 32,
        "Singer, Bill": 32,
        "Moose, Bob": 32,
    },
    "hybrid": {
        "Chance, Dean": 38,
        "Niekro, Phil": 38,
        "Washburn, Ray": 36,
        "Singer, Bill": 36,
        "Moose, Bob": 14,
    },
}

WORKLOAD_BANDS = {
    "conservative": {"S7": 5.5, "S8": 6.0},
    "base": {"S7": 6.0, "S8": 6.5},
    "aggressive": {"S7": 6.5, "S8": 7.0},
}


def read_json(path: Path) -> Any:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def rating(value: object) -> int:
    match = re.search(r"\d+", str(value or ""))
    return int(match.group()) if match else 0


def probability(record: dict[str, Any], key: str) -> float:
    value = record.get(key, {})
    if not isinstance(value, dict):
        return 0.0
    return float(value.get("decimal", 0) or 0)


def injury_limit(innings_pitched: float) -> str:
    if innings_pitched >= 300:
        return "remainder_only"
    if innings_pitched >= 200:
        return "3_extra_games"
    return "15_extra_games"


def weighted_average(
    starts: dict[str, int],
    metrics: dict[str, dict[str, Any]],
    side: str,
    metric: str,
) -> float:
    total_starts = sum(starts.values())
    if total_starts == 0:
        return 0.0

    return (
        sum(
            metrics[player]["sides"][side][metric] * count
            for player, count in starts.items()
        )
        / total_starts
    )


def markdown_table(
    headers: list[str],
    rows: list[list[object]],
) -> list[str]:
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(str(value) for value in row) + " |")
    return lines


fixture = read_json(FIXTURE_PATH)

with MECHANICS_PATH.open(encoding="utf-8", newline="") as handle:
    mechanics_rows = list(csv.DictReader(handle))

metadata_document = read_json(METADATA_PATH)
metadata_rows = metadata_document["players"]

mechanics_by_name = {
    row["playerName"]: row
    for row in mechanics_rows
}
metadata_by_name = {
    row["playerName"]: row
    for row in metadata_rows
}

required_names = set(ROTATION + FINALISTS)

missing_mechanics = sorted(
    name for name in required_names
    if name not in mechanics_by_name
)
missing_metadata = sorted(
    name for name in required_names
    if name not in metadata_by_name
)

if missing_mechanics:
    raise RuntimeError(
        "Missing pitcher mechanics: " + "; ".join(missing_mechanics)
    )

if missing_metadata:
    raise RuntimeError(
        "Missing pitcher metadata: " + "; ".join(missing_metadata)
    )

metrics: dict[str, dict[str, Any]] = {}

for name in sorted(required_names):
    mechanics = mechanics_by_name[name]
    summary_path = CARD_ROOT / (
        mechanics["playerId"] + ".card-probability-summary.json"
    )

    if not summary_path.exists():
        raise RuntimeError(f"Missing card summary for {name}: {summary_path}")

    summary = read_json(summary_path)
    summary_sides = {
        side["side"]: side
        for side in summary["sides"]
    }

    sides: dict[str, dict[str, float]] = {}

    for side_name in ("vs_left_batter", "vs_right_batter"):
        side = summary_sides[side_name]
        outcomes = side["baseOutcomeWeights"]
        dependencies = side["dependencyWeights"]

        sides[side_name] = {
            "on_base": probability(side, "onBaseCandidateWeight"),
            "hit": probability(side, "hitCandidateWeight"),
            "walk": probability(outcomes, "WALK"),
            "single": probability(outcomes, "SINGLE"),
            "double": probability(outcomes, "DOUBLE"),
            "triple": probability(outcomes, "TRIPLE"),
            "home_run": probability(outcomes, "HOME_RUN"),
            "strikeout": probability(outcomes, "STRIKEOUT"),
            "groundball": probability(outcomes, "GROUNDBALL"),
            "flyball": probability(outcomes, "FLYBALL"),
            "ballpark_home_run_check": probability(
                dependencies,
                "ballpark_home_run_check",
            ),
            "ballpark_single_check": probability(
                dependencies,
                "ballpark_single_check",
            ),
            "defensive_x_chart": probability(
                dependencies,
                "defensive_x_chart",
            ),
        }

    innings_pitched = float(
        metadata_by_name[name]["pitcherStats"]["inningsPitched"]
    )

    salary = float(
        str(mechanics["salary"]).replace("$", "") or 0
    )

    metrics[name] = {
        "player_id": mechanics["playerId"],
        "salary_millions": salary,
        "throws": mechanics["throws"],
        "starter_endurance": rating(mechanics["starterEndurance"]),
        "relief_endurance": rating(mechanics["reliefEndurance"]),
        "closer_endurance": rating(mechanics["closerEndurance"]),
        "pitcher_defense": mechanics["pitcherFieldingRating"],
        "astrodome_score": float(
            mechanics["astrodomeParkAdjustedBrowserScore"] or 0
        ),
        "real_life_innings_pitched": innings_pitched,
        "injury_limit": injury_limit(innings_pitched),
        "sides": sides,
    }

architecture_rows: list[dict[str, Any]] = []

for architecture, starts in START_ARCHITECTURES.items():
    left_ob = weighted_average(
        starts,
        metrics,
        "vs_left_batter",
        "on_base",
    )
    right_ob = weighted_average(
        starts,
        metrics,
        "vs_right_batter",
        "on_base",
    )
    left_hr = weighted_average(
        starts,
        metrics,
        "vs_left_batter",
        "home_run",
    )
    right_hr = weighted_average(
        starts,
        metrics,
        "vs_right_batter",
        "home_run",
    )

    architecture_rows.append(
        {
            "architecture": architecture,
            "starts": starts,
            "total_starts": sum(starts.values()),
            "moose_starts": starts["Moose, Bob"],
            "left_ob": left_ob,
            "right_ob": right_ob,
            "ob_40_percent_left": 0.4 * left_ob + 0.6 * right_ob,
            "ob_50_percent_left": 0.5 * left_ob + 0.5 * right_ob,
            "ob_60_percent_left": 0.6 * left_ob + 0.4 * right_ob,
            "left_hr": left_hr,
            "right_hr": right_hr,
        }
    )

workload_rows: list[dict[str, Any]] = []
regulation_innings = 162 * 9

for architecture, starts in START_ARCHITECTURES.items():
    for band, rates in WORKLOAD_BANDS.items():
        starter_innings = 0.0

        for player, start_count in starts.items():
            endurance = metrics[player]["starter_endurance"]
            rate_key = "S8" if endurance >= 8 else "S7"
            starter_innings += start_count * rates[rate_key]

        bullpen_innings = regulation_innings - starter_innings

        workload_rows.append(
            {
                "architecture": architecture,
                "workload_band": band,
                "starter_innings": starter_innings,
                "bullpen_innings": bullpen_innings,
                "bullpen_innings_per_game": bullpen_innings / 162,
            }
        )

rotation_schedule = [
    ROTATION[index % len(ROTATION)]
    for index in range(162)
]

single_injury_stress: dict[str, dict[str, Any]] = {}

for pitcher in ROTATION:
    missed_starts: list[int] = []

    for injury_start in range(162):
        missed = sum(
            rotation_schedule[index] == pitcher
            for index in range(
                injury_start + 1,
                min(injury_start + 4, 162),
            )
        )
        missed_starts.append(missed)

    single_injury_stress[pitcher] = {
        "maximum_missed_starts": max(missed_starts),
        "windows_requiring_swingman": sum(
            value > 0 for value in missed_starts
        ),
        "average_missed_starts": (
            sum(missed_starts) / len(missed_starts)
        ),
    }

dual_injury_stress: dict[str, dict[str, Any]] = {}

for first, second in combinations(ROTATION, 2):
    missed_starts = []

    for injury_start in range(162):
        missed = sum(
            rotation_schedule[index] in {first, second}
            for index in range(
                injury_start + 1,
                min(injury_start + 4, 162),
            )
        )
        missed_starts.append(missed)

    key = f"{first} + {second}"

    dual_injury_stress[key] = {
        "maximum_missed_starts": max(missed_starts),
        "maximum_uncovered_with_one_swingman": max(
            max(0, value - 1)
            for value in missed_starts
        ),
        "windows_with_uncovered_start": sum(
            value > 1 for value in missed_starts
        ),
    }

moose = metrics[CURRENT_SWINGMAN]
jackson = metrics[PRIMARY_ALTERNATIVE_SWINGMAN]

moose_left = moose["sides"]["vs_left_batter"]["on_base"]
moose_right = moose["sides"]["vs_right_batter"]["on_base"]
jackson_left = jackson["sides"]["vs_left_batter"]["on_base"]
jackson_right = jackson["sides"]["vs_right_batter"]["on_base"]

denominator = (
    (jackson_left - jackson_right)
    - (moose_left - moose_right)
)

left_batter_break_even = (
    (moose_right - jackson_right) / denominator
    if denominator
    else None
)

current_roster_salary = sum(
    float(player["salaryMillions"])
    for player in fixture["players"]
)

projected_roster_salary = (
    current_roster_salary
    - moose["salary_millions"]
    + jackson["salary_millions"]
)

finalist_rows = []

for name in FINALISTS:
    player = metrics[name]
    left = player["sides"]["vs_left_batter"]
    right = player["sides"]["vs_right_batter"]

    finalist_rows.append(
        {
            "player": name,
            "salary_millions": player["salary_millions"],
            "starter_endurance": player["starter_endurance"],
            "relief_endurance": player["relief_endurance"],
            "throws": player["throws"],
            "pitcher_defense": player["pitcher_defense"],
            "astrodome_score": player["astrodome_score"],
            "injury_limit": player["injury_limit"],
            "left_ob": left["on_base"],
            "right_ob": right["on_base"],
            "average_ob": (
                left["on_base"] + right["on_base"]
            ) / 2,
            "left_hr": left["home_run"],
            "right_hr": right["home_run"],
        }
    )

report = {
    "schemaVersion": "bie.1968.astrodome-pitching-architecture.v0",
    "season": 1968,
    "park": "Astrodome",
    "methodology": {
        "balance_labels": (
            "Metadata only. Recommendations use extracted card-side "
            "outcomes against left-handed and right-handed batters."
        ),
        "real_life_usage": (
            "Real-life innings are used only to derive the Strat injury "
            "ceiling, not to project BIE deployment."
        ),
        "workload_model": (
            "Workload is tested as explicit sensitivity bands rather "
            "than presented as an exact fatigue forecast."
        ),
    },
    "current_staff": {
        "rotation": ROTATION,
        "current_swingman": CURRENT_SWINGMAN,
        "current_roster_salary_millions": current_roster_salary,
    },
    "architecture_comparison": architecture_rows,
    "workload_sensitivity": workload_rows,
    "injury_stress": {
        "single_starter": single_injury_stress,
        "two_starter_overlap": dual_injury_stress,
    },
    "swingman_finalists": finalist_rows,
    "recommendation": {
        "architecture": "four_man_starred",
        "rotation": ROTATION,
        "swingman": CURRENT_SWINGMAN,
        "primary_alternative_swingman": PRIMARY_ALTERNATIVE_SWINGMAN,
        "normal_planned_swingman_starts": 0,
        "swingman_roles": [
            "long relief",
            "first emergency starter",
            "selective start against a left-heavy lineup",
        ],
        "current_swingman_disposition": (
            "Bob Moose remains the baseline swingman. Al Jackson is "
            "the preferred left-handed and salary-saving alternative."
        ),
        "left_batter_break_even_share": left_batter_break_even,
        "alternative_salary_change_millions": (
            jackson["salary_millions"]
            - moose["salary_millions"]
        ),
        "alternative_roster_salary_millions": projected_roster_salary,
        "alternative_cap_room_millions": (
            CAP_MILLIONS - projected_roster_salary
        ),
        "dual_injury_policy": (
            "One swingman covers one missed turn. Two simultaneous "
            "rotation injuries may require an emergency free-agent move."
        ),
        "rationale": [
            (
                "The four-man rotation produced the strongest extracted "
                "card-side on-base suppression at every tested LHB mix."
            ),
            (
                "Bullpen workload was effectively unchanged across the "
                "four-man, five-man and hybrid architectures."
            ),
            (
                "Each starred rotation member carries a three-extra-game "
                "injury ceiling and can lose at most one scheduled turn "
                "during that absence."
            ),
            (
                "Bob Moose remains the baseline swingman because his "
                "card has strong Astrodome characteristics, no direct "
                "home-run outcomes, and better pitcher defense."
            ),
            (
                "Al Jackson is the preferred left-handed and "
                "salary-saving alternative when league composition, "
                "opponent mix, or another roster upgrade justifies it."
            ),
        ],
    },
}

OUTPUT_JSON.parent.mkdir(parents=True, exist_ok=True)

OUTPUT_JSON.write_text(
    json.dumps(report, indent=2) + "\n",
    encoding="utf-8",
)

markdown: list[str] = [
    "# 1968 Astrodome Pitching Architecture v0",
    "",
    "## Executive Recommendation",
    "",
    (
        "Use a four-man starred rotation of Dean Chance, Phil Niekro, "
        "Ray Washburn, and Bill Singer."
    ),
    "",
    (
        "Use Bob Moose as the baseline fifth starter-rated pitcher, "
        "swingman, long reliever, and first emergency starter."
    ),
    "",
    (
        "Use Al Jackson as the preferred left-handed and salary-saving "
        "alternative rather than a mandatory canonical replacement."
    ),
    "",
    "## Methodology",
    "",
    (
        "- Published balance labels are metadata only. Analytical "
        "judgments use extracted card outcomes against LHB and RHB."
    ),
    (
        "- Real-life innings are used only to derive pitcher injury "
        "ceilings."
    ),
    (
        "- Fatigue workload is presented as sensitivity bands, not as "
        "an invented exact forecast."
    ),
    "",
    "## Architecture Card-Side Comparison",
    "",
]

markdown.extend(
    markdown_table(
        [
            "Architecture",
            "Moose Starts",
            "LHB OB",
            "RHB OB",
            "40% LHB",
            "50% LHB",
            "60% LHB",
        ],
        [
            [
                row["architecture"],
                row["moose_starts"],
                f"{row['left_ob']:.4f}",
                f"{row['right_ob']:.4f}",
                f"{row['ob_40_percent_left']:.4f}",
                f"{row['ob_50_percent_left']:.4f}",
                f"{row['ob_60_percent_left']:.4f}",
            ]
            for row in architecture_rows
        ],
    )
)

markdown.extend(
    [
        "",
        "## Bullpen Workload Sensitivity",
        "",
    ]
)

markdown.extend(
    markdown_table(
        [
            "Architecture",
            "Band",
            "Starter IP",
            "Bullpen IP",
            "Bullpen IP/Game",
        ],
        [
            [
                row["architecture"],
                row["workload_band"],
                f"{row['starter_innings']:.1f}",
                f"{row['bullpen_innings']:.1f}",
                f"{row['bullpen_innings_per_game']:.2f}",
            ]
            for row in workload_rows
        ],
    )
)

markdown.extend(
    [
        "",
        "## Swingman Finalists",
        "",
    ]
)

markdown.extend(
    markdown_table(
        [
            "Pitcher",
            "Salary",
            "Role",
            "Throws",
            "LHB OB",
            "RHB OB",
            "Average OB",
            "LHB HR",
            "RHB HR",
            "Defense",
            "Injury",
        ],
        [
            [
                row["player"],
                f"${row['salary_millions']:.2f}M",
                (
                    f"S{row['starter_endurance']}/"
                    f"R{row['relief_endurance']}"
                ),
                row["throws"],
                f"{row['left_ob']:.4f}",
                f"{row['right_ob']:.4f}",
                f"{row['average_ob']:.4f}",
                f"{row['left_hr']:.4f}",
                f"{row['right_hr']:.4f}",
                row["pitcher_defense"],
                row["injury_limit"],
            ]
            for row in finalist_rows
        ],
    )
)

markdown.extend(
    [
        "",
        "## Injury Resilience",
        "",
        (
            "Each primary starter can miss at most one scheduled start "
            "during a three-team-game absence."
        ),
        "",
        (
            "One swingman covers that missed turn. Two overlapping "
            "starter injuries can create one uncovered start and should "
            "trigger the emergency free-agent list."
        ),
        "",
        "## Alternative Salary Effect",
        "",
        (
            f"- Current roster: ${current_roster_salary:.2f}M"
        ),
        (
            f"- Alternative roster with Al Jackson: "
            f"${projected_roster_salary:.2f}M"
        ),
        (
            f"- Alternative cap room: "
            f"${CAP_MILLIONS - projected_roster_salary:.2f}M"
        ),
        "",
        "## Operational Policy",
        "",
        "1. Use the four starred starters in regular rotation.",
        "2. Do not schedule routine fifth-starter turns.",
        (
            "3. Use Bob Moose for long relief and first-line injury "
            "coverage."
        ),
        (
            "4. Keep Al Jackson as the preferred left-handed and "
            "salary-saving alternative."
        ),
        (
            "5. Maintain an emergency free-agent starter list for "
            "overlapping rotation injuries."
        ),
        "",
    ]
)

OUTPUT_MD.write_text(
    "\n".join(markdown),
    encoding="utf-8",
)

print("# RESULT SUMMARY")
print(f"REPORT_JSON: {OUTPUT_JSON.relative_to(ROOT)}")
print(f"REPORT_MD: {OUTPUT_MD.relative_to(ROOT)}")
print("ARCHITECTURE: four_man_starred")
print(f"ROTATION: {'; '.join(ROTATION)}")
print(f"BASELINE_SWINGMAN: {CURRENT_SWINGMAN}")
print(
    "PRIMARY_ALTERNATIVE_SWINGMAN: "
    f"{PRIMARY_ALTERNATIVE_SWINGMAN}"
)
print(
    "LHB_BREAK_EVEN_SHARE: "
    f"{left_batter_break_even:.4f}"
)
print(
    "PROJECTED_ROSTER_SALARY: "
    f"{projected_roster_salary:.2f}M"
)
print(
    "PROJECTED_CAP_ROOM: "
    f"{CAP_MILLIONS - projected_roster_salary:.2f}M"
)