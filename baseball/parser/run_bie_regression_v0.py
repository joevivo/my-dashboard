import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

VERIFY_SCRIPTS = [
    "verify_parser_sample_v0.py",
    "verify_parser_full_corpus_v0.py",
    "verify_result_cells_v0.py",
    "verify_normalized_result_labels_v0.py",
    "verify_split_ranges_v0.py",
    "verify_result_modifiers_v0.py",
    "verify_result_atoms_v0.py",
    "verify_result_semantics_v0.py",
    "verify_result_probabilities_v0.py",
    "verify_card_probability_summaries_v0.py",
    "verify_matchup_probabilities_v0.py",
    "verify_matchup_player_profiles_v0.py",
    "verify_neutral_draft_signals_v0.py",
    "verify_salary_adjusted_draft_signals_v0.py",
    "verify_player_roster_metadata_v0.py",
    "verify_player_defense_metadata_v0.py",
    "verify_defensive_draft_signals_v0.py",
    "verify_defense_aware_draft_signals_v0.py",
    "verify_ballparks_v0.py",
    "verify_ballpark_aware_draft_signals_v0.py",
    "evaluate_roster_construction_v0.py",
    "verify_roster_construction_v0.py",
    "verify_roster_template_evaluator_v0.py",
    "verify_strat365_team_importer_v0.py",
    "parse_observed_player_results_v0.py",
    "verify_observed_player_results_v0.py",
    "verify_batch_observed_player_results_v0.py",
    "report_observed_player_batch_calibration_v0.py",
    "report_observed_player_aggregate_calibration_v0.py",
]

def main():
    parser_dir = ROOT / "baseball" / "parser"
    failures = []

    print("# BIE Regression v0")
    print()

    for script in VERIFY_SCRIPTS:
        path = parser_dir / script

        if not path.exists():
            print(f"MISS: {script}")
            failures.append(script)
            continue

        print(f"RUN : {script}")
        result = subprocess.run(
            [sys.executable, str(path)],
            cwd=ROOT,
            text=True,
            capture_output=True,
        )

        if result.stdout.strip():
            print(result.stdout.strip())

        if result.returncode != 0:
            print(result.stderr.strip())
            print(f"FAIL: {script}")
            failures.append(script)
        else:
            print(f"PASS: {script}")

        print()

    if failures:
        print("Regression failed:")
        for failure in failures:
            print(f"- {failure}")
        raise SystemExit(1)

    print("PASS: full BIE regression")

if __name__ == "__main__":
    main()
