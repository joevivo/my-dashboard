import csv
import tempfile
from pathlib import Path

import evaluate_roster_template_v0 as evaluator


SAMPLE_ROWS = [
    ("Moore, Charlie", "C"),
    ("Cooper, Cecil", "1B"),
    ("Gantner, Jim", "2B"),
    ("Randle, Lenny", "3B"),
    ("Foli, Tim", "SS"),
    ("Piniella, Lou", "LF"),
    ("Collins, Dave", "CF"),
    ("Smith, Reggie", "RF"),
    ("Martin, John", "starter"),
    ("Hough, Charlie", "starter"),
    ("Bystrom, Marty", "starter"),
    ("Richard, J.r.", "starter"),
    ("Martinez, Tippy", "relief"),
    ("Kinney, Dennis", "relief"),
    ("Rawley, Shane", "relief"),
    ("Holland, Al", "relief"),
]


def write_sample_roster(path):
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["playerName", "slot"])
        writer.writerows(SAMPLE_ROWS)


def main():
    ballpark_payload = evaluator.load_json(evaluator.DEFAULT_BALLPARK_AWARE_PATH)
    defense_payload = evaluator.load_json(evaluator.DEFAULT_DEFENSE_AWARE_PATH)
    defense_metadata_payload = evaluator.load_json(evaluator.DEFAULT_DEFENSE_METADATA_PATH)
    by_id, by_name = evaluator.build_player_lookup(ballpark_payload, defense_payload)
    position_lookup = evaluator.build_position_lookup(defense_metadata_payload)

    brett_matches = [
        row for row in ballpark_payload["hitters"]
        if row.get("player", {}).get("playerName") == "Brett, George"
    ]
    assert brett_matches, "Expected to find Brett, George"
    brett_positions = position_lookup.get(str(evaluator.player_id(brett_matches[0])), [])
    assert "1B" in brett_positions, "Expected Brett, George to qualify at 1B"

    with tempfile.TemporaryDirectory() as temp_dir:
        roster_path = Path(temp_dir) / "sample-roster.csv"
        write_sample_roster(roster_path)

        rows, unresolved = evaluator.load_roster(roster_path, by_id, by_name)
        assert len(rows) == 16, f"Expected 16 resolved rows, got {len(rows)}"
        assert len(unresolved) == 0, f"Expected 0 unresolved rows, got {len(unresolved)}"

        salary_totals = evaluator.bucket_salary(rows)
        coverage = evaluator.position_coverage(rows, position_lookup)
        archetype = evaluator.ARCHETYPES["value-spine"]

        score, flags, risk_items = evaluator.archetype_score(
            rows,
            unresolved,
            salary_totals,
            archetype,
            coverage,
            evaluator.DEFAULT_BALLPARK_NAME,
            80.0,
        )

        assert score == 72, f"Expected value-spine score 72, got {score}"
        assert round(sum(salary_totals.values()), 2) == 54.78
        assert all(coverage[position] for position in evaluator.REQUIRED_POSITIONS)
        assert len(risk_items) == 8, f"Expected 8 risk players, got {len(risk_items)}"

    print("PASS: roster template evaluator smoke verification")
    print(f"Resolved rows: {len(rows)}")
    print(f"Score: {score}")
    print(f"Salary total: ${sum(salary_totals.values()):.2f}M")
    print(f"Risk players: {len(risk_items)}")


if __name__ == "__main__":
    main()
