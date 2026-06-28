from __future__ import annotations

from pathlib import Path
import json
from typing import Any


SAMPLE_PATH = Path("baseball/parser/sample_set_v0.json")
PARSED_DIR = Path("data/baseball/parsed/strat365/1980/cards")


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig", errors="replace"))


def fail(message: str) -> None:
    raise AssertionError(message)


def verify_card(sample_player: dict[str, Any]) -> None:
    player_id = int(sample_player["playerId"])
    expected_role = sample_player["role"]

    parsed_path = PARSED_DIR / f"{player_id}.parsed-card-evidence.json"
    if not parsed_path.exists():
        fail(f"Missing parsed output for {player_id}: {parsed_path}")

    data = read_json(parsed_path)

    if data.get("schemaVersion") != "bie.parsed-card-evidence.v0":
        fail(f"{player_id}: unexpected schemaVersion {data.get('schemaVersion')}")

    if data.get("role") != expected_role:
        fail(f"{player_id}: expected role {expected_role}, found {data.get('role')}")

    if data.get("source", {}).get("captureStatus") != "validated_authenticated_card":
        fail(f"{player_id}: source capture status is not validated_authenticated_card")

    if data.get("player", {}).get("playerId") != player_id:
        fail(f"{player_id}: playerId mismatch")

    if not data.get("card", {}).get("balance"):
        fail(f"{player_id}: missing balance")

    result_evidence = data.get("resultEvidence", [])
    if len(result_evidence) != 6:
        fail(f"{player_id}: expected 6 result evidence sections, found {len(result_evidence)}")

    for idx, item in enumerate(result_evidence, start=1):
        if not item.get("rawResultText"):
            fail(f"{player_id}: result evidence {idx} missing rawResultText")

        source = item.get("source", {})
        if source.get("kind") != "html_table":
            fail(f"{player_id}: result evidence {idx} source kind is not html_table")

        if not source.get("pointer"):
            fail(f"{player_id}: result evidence {idx} missing source pointer")

    warnings = data.get("warnings", [])
    if warnings:
        fail(f"{player_id}: expected no warnings, found {warnings}")

    if expected_role == "hitter":
        traits = data.get("hitterTraits") or {}
        if not traits.get("defenseText"):
            fail(f"{player_id}: hitter missing defenseText")
        if not traits.get("runningText"):
            fail(f"{player_id}: hitter missing runningText")
        if data.get("pitcherTraits") is not None:
            fail(f"{player_id}: hitter should not have pitcherTraits")

    if expected_role == "pitcher":
        traits = data.get("pitcherTraits") or {}
        if not traits.get("throws"):
            fail(f"{player_id}: pitcher missing throws")
        if traits.get("hold") is None:
            fail(f"{player_id}: pitcher missing hold")
        if not traits.get("pitcherText"):
            fail(f"{player_id}: pitcher missing pitcherText")
        if data.get("hitterTraits") is not None:
            fail(f"{player_id}: pitcher should not have hitterTraits")


def main() -> None:
    sample = read_json(SAMPLE_PATH)

    print("BIE Parser v0 Sample Verification")
    print("=" * 72)

    players = sample.get("players", [])
    if len(players) != 6:
        fail(f"Expected 6 sample players, found {len(players)}")

    for player in players:
        verify_card(player)
        print(f"OK {player['playerId']} {player['playerName']} role={player['role']}")

    print("-" * 72)
    print("PARSER SAMPLE VERIFIED")
    print("=" * 72)


if __name__ == "__main__":
    main()
