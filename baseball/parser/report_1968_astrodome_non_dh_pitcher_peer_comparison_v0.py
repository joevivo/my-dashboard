from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


ROOT = Path.cwd()

ROSTER_PATH = ROOT / (
    "data/baseball/fixtures/rosters/"
    "1968_astrodome_alou_freehan_chance_parker_v0.json"
)

SIGNAL_PATH = ROOT / (
    "data/baseball/parsed/strat365/1968/draft-signals/"
    "1968.browser-baseline-draft-signals.json"
)

CARD_DIRECTORY = ROOT / (
    "data/baseball/parsed/strat365/1968/cards"
)

JSON_OUTPUT_PATH = ROOT / (
    "data/baseball/parsed/strat365/1968/reports/"
    "1968.astrodome-non-dh-pitcher-peer-comparison-v0.json"
)

MARKDOWN_OUTPUT_PATH = ROOT / (
    "data/baseball/parsed/strat365/1968/reports/"
    "1968.astrodome-non-dh-pitcher-peer-comparison-v0.md"
)

SALARY_CAP = 80.0
NEAR_PITCHING_SCORE_RATIO = 0.97

BAT_CODE_PATTERN = re.compile(
    r"\b([1-8][NW][RLS])\b",
    re.IGNORECASE,
)

RELIEF_PATTERN = re.compile(
    r"relief\((\d+)\)/(\d+)",
    re.IGNORECASE,
)


def read_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8-sig") as handle:
        value = json.load(handle)

    if not isinstance(value, dict):
        raise ValueError(f"Expected JSON object: {path}")

    return value


def safe_float(value: Any) -> float | None:
    try:
        if value is None or value == "":
            return None

        return float(value)
    except (TypeError, ValueError):
        return None


def classify_role(endurance: str) -> str:
    normalized = endurance.strip().upper()

    if normalized.startswith("S"):
        return "starter_or_swingman"

    if normalized.startswith("R"):
        return "pure_reliever"

    return "unknown"


def parse_closer_rating(relief_text: str) -> int:
    match = RELIEF_PATTERN.search(relief_text or "")

    if not match:
        return 0

    return int(match.group(2))


def load_card_evidence(
    player_id: int,
) -> dict[str, Any] | None:
    card_path = CARD_DIRECTORY / (
        f"{player_id}.parsed-card-evidence.json"
    )

    if not card_path.exists():
        return None

    text = card_path.read_text(encoding="utf-8-sig")

    bat_codes = sorted(
        {
            match.group(1).upper()
            for match in BAT_CODE_PATTERN.finditer(text)
        }
    )

    if len(bat_codes) != 1:
        return None

    document = json.loads(text)
    pitcher_traits = document.get("pitcherTraits") or {}

    batting_code = bat_codes[0]
    relief_text = str(
        pitcher_traits.get("reliefText") or ""
    )

    return {
        "cardEvidenceFile": str(
            card_path.relative_to(ROOT)
        ).replace("\\", "/"),
        "battingCode": batting_code,
        "hittingCard": int(batting_code[0]),
        "power": batting_code[1],
        "bats": batting_code[2],
        "bunting": str(
            pitcher_traits.get("buntingText") or ""
        ).strip().upper(),
        "starterText": str(
            pitcher_traits.get("starterText") or ""
        ),
        "reliefText": relief_text,
        "closerRating": parse_closer_rating(
            relief_text
        ),
    }


def structural_match(
    canonical: dict[str, Any],
    candidate: dict[str, Any],
) -> bool:
    if candidate["role"] != canonical["role"]:
        return False

    if (
        canonical["starEligible"]
        and not candidate["starEligible"]
    ):
        return False

    if (
        canonical["hasReliefEndurance"]
        and not candidate["hasReliefEndurance"]
    ):
        return False

    if (
        canonical["role"] == "pure_reliever"
        and canonical["closerRating"] > 0
        and candidate["closerRating"] <= 0
    ):
        return False

    return True


def candidate_summary(
    candidate: dict[str, Any],
    canonical: dict[str, Any],
) -> dict[str, Any]:
    score_delta = round(
        candidate["baselineScore"]
        - canonical["baselineScore"],
        6,
    )

    salary_delta = round(
        candidate["salary"]
        - canonical["salary"],
        2,
    )

    return {
        "playerName": candidate["playerName"],
        "playerId": candidate["playerId"],
        "team": candidate["team"],
        "salary": candidate["salary"],
        "salaryDelta": salary_delta,
        "endurance": candidate["endurance"],
        "battingCode": candidate["battingCode"],
        "hittingCard": candidate["hittingCard"],
        "bunting": candidate["bunting"],
        "baselineScore": candidate["baselineScore"],
        "baselineScoreDelta": score_delta,
        "closerRating": candidate["closerRating"],
    }


errors: list[str] = []

roster = read_json(ROSTER_PATH)
signals = read_json(SIGNAL_PATH)

roster_players = roster.get("players") or []
canonical_pitchers = [
    player
    for player in roster_players
    if player.get("type") == "pitcher"
]

roster_salary = round(
    sum(
        float(player.get("salaryMillions") or 0)
        for player in roster_players
    ),
    2,
)

cap_room = round(
    SALARY_CAP - roster_salary,
    2,
)

canonical_names = {
    str(player.get("name") or "")
    for player in canonical_pitchers
}

pool: list[dict[str, Any]] = []
missing_card_count = 0
ambiguous_card_count = 0

for signal_row in signals.get("pitchers") or []:
    player = signal_row.get("player") or {}
    pitcher = signal_row.get("pitcher") or {}

    player_name = str(
        player.get("playerName") or ""
    ).strip()

    player_id_value = player.get("playerId")

    if not player_name or player_id_value is None:
        continue

    player_id = int(player_id_value)
    endurance = str(
        pitcher.get("endurance") or ""
    ).strip()

    salary_value = signal_row.get("salary")

    if isinstance(salary_value, dict):
        salary_value = salary_value.get("millions")

    salary = safe_float(salary_value)

    baseline_score_value = signal_row.get(
        "browserBaselineDraftScore"
    )

    if isinstance(baseline_score_value, dict):
        baseline_score_value = (
            baseline_score_value.get("score")
        )

    baseline_score = safe_float(
        baseline_score_value
    )

    card_path = CARD_DIRECTORY / (
        f"{player_id}.parsed-card-evidence.json"
    )

    if not card_path.exists():
        missing_card_count += 1
        continue

    card_evidence = load_card_evidence(
        player_id
    )

    if card_evidence is None:
        ambiguous_card_count += 1
        continue

    role = classify_role(endurance)

    if (
        role == "unknown"
        or salary is None
        or baseline_score is None
    ):
        continue

    row = {
        "playerName": player_name,
        "playerId": player_id,
        "team": str(player.get("team") or ""),
        "salary": round(salary, 2),
        "endurance": endurance,
        "role": role,
        "starEligible": "*" in endurance,
        "hasReliefEndurance": "/R" in endurance.upper(),
        "baselineScore": baseline_score,
        **card_evidence,
    }

    pool.append(row)

pool_by_name = {
    row["playerName"]: row
    for row in pool
}

canonical_rows: list[dict[str, Any]] = []

for roster_pitcher in canonical_pitchers:
    player_name = str(
        roster_pitcher.get("name") or ""
    )

    canonical_row = pool_by_name.get(
        player_name
    )

    if canonical_row is None:
        errors.append(
            f"Canonical pitcher unavailable in "
            f"evaluated pool: {player_name}"
        )
        continue

    direct_salary_limit = round(
        canonical_row["salary"] + cap_room,
        2,
    )

    structural_peers = [
        candidate
        for candidate in pool
        if (
            candidate["playerName"]
            not in canonical_names
            and candidate["salary"]
            <= direct_salary_limit
            and structural_match(
                canonical_row,
                candidate,
            )
        )
    ]

    strict_upgrades = [
        candidate
        for candidate in structural_peers
        if (
            candidate["hittingCard"]
            > canonical_row["hittingCard"]
            and candidate["baselineScore"]
            >= canonical_row["baselineScore"]
        )
    ]

    near_pitching_tradeoffs = [
        candidate
        for candidate in structural_peers
        if (
            candidate["hittingCard"]
            > canonical_row["hittingCard"]
            and candidate["baselineScore"]
            < canonical_row["baselineScore"]
            and candidate["baselineScore"]
            >= (
                canonical_row["baselineScore"]
                * NEAR_PITCHING_SCORE_RATIO
            )
        )
    ]

    strict_upgrades.sort(
        key=lambda candidate: (
            -candidate["baselineScore"],
            -candidate["hittingCard"],
            candidate["salary"],
            candidate["playerName"],
        )
    )

    near_pitching_tradeoffs.sort(
        key=lambda candidate: (
            -candidate["hittingCard"],
            -candidate["baselineScore"],
            candidate["salary"],
            candidate["playerName"],
        )
    )

    canonical_rows.append(
        {
            **canonical_row,
            "directSalaryLimit": direct_salary_limit,
            "structuralPeerCount": len(
                structural_peers
            ),
            "strictUpgradeCount": len(
                strict_upgrades
            ),
            "nearPitchingTradeoffCount": len(
                near_pitching_tradeoffs
            ),
            "strictUpgrades": [
                candidate_summary(
                    candidate,
                    canonical_row,
                )
                for candidate in strict_upgrades[:5]
            ],
            "nearPitchingTradeoffs": [
                candidate_summary(
                    candidate,
                    canonical_row,
                )
                for candidate
                in near_pitching_tradeoffs[:5]
            ],
        }
    )

canonical_rows.sort(
    key=lambda row: (
        0
        if row["role"]
        == "starter_or_swingman"
        else 1,
        -row["baselineScore"],
        row["playerName"],
    )
)

strict_upgrade_pair_count = sum(
    row["strictUpgradeCount"]
    for row in canonical_rows
)

canonical_with_strict_upgrade = [
    row["playerName"]
    for row in canonical_rows
    if row["strictUpgradeCount"] > 0
]

tradeoff_pair_count = sum(
    row["nearPitchingTradeoffCount"]
    for row in canonical_rows
)

report_pass = (
    len(signals.get("pitchers") or []) == 212
    and len(canonical_pitchers) == 11
    and len(canonical_rows) == 11
    and not errors
)

report = {
    "schemaVersion": (
        "1968.astrodome.non-dh-pitcher-"
        "peer-comparison.v0"
    ),
    "season": 1968,
    "park": "Astrodome",
    "leagueFormat": "non-DH",
    "sourceRoster": str(
        ROSTER_PATH.relative_to(ROOT)
    ).replace("\\", "/"),
    "salaryCap": SALARY_CAP,
    "rosterSalary": roster_salary,
    "capRoom": cap_room,
    "method": {
        "strictUpgrade": [
            "same pitcher role",
            "preserve star eligibility when required",
            "preserve relief endurance when required",
            "preserve closer capability for relievers",
            "affordable as a one-for-one replacement",
            "equal-or-better baseline pitching score",
            "better pitcher-hitting card",
        ],
        "nearPitchingTradeoff": (
            "Better hitting card with at least "
            "97% of the canonical baseline "
            "pitching score."
        ),
        "automaticRecommendation": False,
    },
    "summary": {
        "fullPitcherDatasetCount": len(
            signals.get("pitchers") or []
        ),
        "evaluatedCardBackedPitcherCount": len(
            pool
        ),
        "missingCardFileCount": missing_card_count,
        "ambiguousCardCodeCount": (
            ambiguous_card_count
        ),
        "canonicalPitcherCount": len(
            canonical_rows
        ),
        "strictUpgradePairCount": (
            strict_upgrade_pair_count
        ),
        "canonicalWithStrictUpgradeCount": len(
            canonical_with_strict_upgrade
        ),
        "canonicalWithStrictUpgrade": (
            canonical_with_strict_upgrade
        ),
        "nearPitchingTradeoffPairCount": (
            tradeoff_pair_count
        ),
        "reportPass": report_pass,
    },
    "canonicalComparisons": canonical_rows,
    "errors": errors,
}

JSON_OUTPUT_PATH.parent.mkdir(
    parents=True,
    exist_ok=True,
)

JSON_OUTPUT_PATH.write_text(
    json.dumps(
        report,
        indent=2,
        sort_keys=False,
    )
    + "\n",
    encoding="utf-8",
)

markdown: list[str] = [
    "# 1968 Astrodome Non-DH Pitcher Peer Comparison",
    "",
    f"- Full pitcher dataset: **{report['summary']['fullPitcherDatasetCount']}**",
    f"- Evaluated card-backed pitchers: **{len(pool)}**",
    f"- Canonical pitchers: **{len(canonical_rows)}**",
    f"- Strict upgrade pairs: **{strict_upgrade_pair_count}**",
    (
        "- Canonical pitchers with at least one "
        f"strict upgrade: **{len(canonical_with_strict_upgrade)}**"
    ),
    (
        "- Near-pitching tradeoff pairs: "
        f"**{tradeoff_pair_count}**"
    ),
    "",
    "A strict upgrade is not an automatic roster recommendation.",
    "",
    "| Canonical pitcher | Role | Salary | Bat | Bunt | Baseline | Strict upgrades | Near tradeoffs |",
    "|---|---|---:|---:|---|---:|---:|---:|",
]

for row in canonical_rows:
    markdown.append(
        "| "
        f"{row['playerName']} | "
        f"{row['role']} | "
        f"${row['salary']:.2f}M | "
        f"{row['battingCode']} | "
        f"{row['bunting']} | "
        f"{row['baselineScore']:.4f} | "
        f"{row['strictUpgradeCount']} | "
        f"{row['nearPitchingTradeoffCount']} |"
    )

for row in canonical_rows:
    markdown.extend(
        [
            "",
            f"## {row['playerName']}",
            "",
            (
                f"Direct replacement salary limit: "
                f"**${row['directSalaryLimit']:.2f}M**"
            ),
            "",
        ]
    )

    if row["strictUpgrades"]:
        markdown.append("### Strict upgrade candidates")
        markdown.append("")
        markdown.append(
            "| Candidate | Salary | Endurance | Bat | Bunt | Baseline | Score delta |"
        )
        markdown.append(
            "|---|---:|---|---:|---|---:|---:|"
        )

        for candidate in row["strictUpgrades"]:
            markdown.append(
                "| "
                f"{candidate['playerName']} | "
                f"${candidate['salary']:.2f}M | "
                f"{candidate['endurance']} | "
                f"{candidate['battingCode']} | "
                f"{candidate['bunting']} | "
                f"{candidate['baselineScore']:.4f} | "
                f"{candidate['baselineScoreDelta']:+.4f} |"
            )
    else:
        markdown.append(
            "No strict upgrade candidate identified."
        )

MARKDOWN_OUTPUT_PATH.write_text(
    "\n".join(markdown) + "\n",
    encoding="utf-8",
)

print("# RESULT SUMMARY")
print(
    "FULL_PITCHER_DATASET_COUNT: "
    f"{report['summary']['fullPitcherDatasetCount']}"
)
print(
    "EVALUATED_CARD_BACKED_PITCHER_COUNT: "
    f"{report['summary']['evaluatedCardBackedPitcherCount']}"
)
print(
    "MISSING_CARD_FILE_COUNT: "
    f"{report['summary']['missingCardFileCount']}"
)
print(
    "AMBIGUOUS_CARD_CODE_COUNT: "
    f"{report['summary']['ambiguousCardCodeCount']}"
)
print(
    "CANONICAL_PITCHER_COUNT: "
    f"{report['summary']['canonicalPitcherCount']}"
)
print(
    "STRICT_UPGRADE_PAIR_COUNT: "
    f"{strict_upgrade_pair_count}"
)
print(
    "CANONICAL_WITH_STRICT_UPGRADE_COUNT: "
    f"{len(canonical_with_strict_upgrade)}"
)
print(
    "NEAR_PITCHING_TRADEOFF_PAIR_COUNT: "
    f"{tradeoff_pair_count}"
)
print(f"ERROR_COUNT: {len(errors)}")
print(f"REPORT_PASS: {report_pass}")

for row in canonical_rows:
    best_strict = (
        row["strictUpgrades"][0]
        if row["strictUpgrades"]
        else None
    )

    best_tradeoff = (
        row["nearPitchingTradeoffs"][0]
        if row["nearPitchingTradeoffs"]
        else None
    )

    print(
        "CANONICAL_COMPARISON: "
        f"PLAYER={row['playerName']} | "
        f"ROLE={row['role']} | "
        f"SALARY={row['salary']:.2f} | "
        f"BAT={row['battingCode']} | "
        f"BUNT={row['bunting']} | "
        f"BASELINE={row['baselineScore']:.6f} | "
        f"STRICT_UPGRADES={row['strictUpgradeCount']} | "
        f"BEST_STRICT="
        f"{best_strict['playerName'] if best_strict else 'NONE'} | "
        f"NEAR_TRADEOFFS={row['nearPitchingTradeoffCount']} | "
        f"BEST_TRADEOFF="
        f"{best_tradeoff['playerName'] if best_tradeoff else 'NONE'}"
    )

for error in errors:
    print(f"ERROR: {error}")

print(
    "OVERALL: "
    + ("PASS" if report_pass else "FAIL")
)
