from __future__ import annotations

from collections import Counter
from pathlib import Path
import json
from typing import Any


UNIVERSE_PATH = Path("data/baseball/raw/strat365/1980/players/1980_players_universe.json")
PARSED_DIR = Path("data/baseball/parsed/strat365/1980/cards")

EXPECTED_SCHEMA_VERSION = "bie.parsed-card-evidence.v0"
EXPECTED_CAPTURE_STATUS = "validated_authenticated_card"


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig", errors="replace"))


def main() -> None:
    universe = read_json(UNIVERSE_PATH)
    players = universe.get("players", [])
    expected_ids = {int(player["playerId"]): player for player in players}

    parsed_paths = list(PARSED_DIR.glob("*.parsed-card-evidence.json"))
    parsed_ids = {
        int(path.name.replace(".parsed-card-evidence.json", "")): path
        for path in parsed_paths
    }

    missing = sorted(set(expected_ids) - set(parsed_ids))
    extra = sorted(set(parsed_ids) - set(expected_ids))

    status_counts: Counter[str] = Counter()
    role_counts: Counter[str] = Counter()
    warning_cards: list[tuple[int, list[str]]] = []
    failures: list[str] = []

    for player_id, player in sorted(expected_ids.items()):
        path = parsed_ids.get(player_id)
        if not path:
            continue

        data = read_json(path)

        schema_version = data.get("schemaVersion")
        if schema_version != EXPECTED_SCHEMA_VERSION:
            failures.append(f"{player_id}: schemaVersion={schema_version}")

        source = data.get("source", {})
        capture_status = source.get("captureStatus")
        status_counts[capture_status] += 1

        if capture_status != EXPECTED_CAPTURE_STATUS:
            failures.append(f"{player_id}: captureStatus={capture_status}")

        role = data.get("role")
        role_counts[role] += 1

        expected_role = player.get("role")
        if role != expected_role:
            failures.append(f"{player_id}: expected role {expected_role}, found {role}")

        parsed_player = data.get("player", {})
        if parsed_player.get("playerId") != player_id:
            failures.append(f"{player_id}: parsed playerId mismatch")

        if parsed_player.get("playerName") != player.get("playerName"):
            failures.append(
                f"{player_id}: parsed playerName mismatch "
                f"{parsed_player.get('playerName')} != {player.get('playerName')}"
            )

        if not data.get("card", {}).get("balance"):
            failures.append(f"{player_id}: missing balance")

        result_evidence = data.get("resultEvidence", [])
        if len(result_evidence) != 6:
            failures.append(f"{player_id}: expected 6 result sections, found {len(result_evidence)}")

        for idx, item in enumerate(result_evidence, start=1):
            if not item.get("rawResultText"):
                failures.append(f"{player_id}: empty rawResultText at resultEvidence[{idx}]")

            source_pointer = item.get("source", {}).get("pointer")
            if not source_pointer:
                failures.append(f"{player_id}: missing source pointer at resultEvidence[{idx}]")

        if role == "hitter":
            traits = data.get("hitterTraits") or {}
            if not traits.get("defenseText"):
                failures.append(f"{player_id}: hitter missing defenseText")
            if not traits.get("runningText"):
                failures.append(f"{player_id}: hitter missing runningText")
            if data.get("pitcherTraits") is not None:
                failures.append(f"{player_id}: hitter has pitcherTraits")

        if role == "pitcher":
            traits = data.get("pitcherTraits") or {}
            if not traits.get("throws"):
                failures.append(f"{player_id}: pitcher missing throws")
            if traits.get("hold") is None:
                failures.append(f"{player_id}: pitcher missing hold")
            if not traits.get("pitcherText"):
                failures.append(f"{player_id}: pitcher missing pitcherText")
            if data.get("hitterTraits") is not None:
                failures.append(f"{player_id}: pitcher has hitterTraits")

        warnings = data.get("warnings", [])
        if warnings:
            warning_cards.append((player_id, warnings))

    print("BIE Parser v0 Full-Corpus Verification")
    print("=" * 72)
    print(f"Universe players: {len(expected_ids)}")
    print(f"Parsed files: {len(parsed_ids)}")
    print(f"Missing parsed files: {len(missing)}")
    print(f"Extra parsed files: {len(extra)}")
    print(f"Capture status counts: {dict(status_counts)}")
    print(f"Role counts: {dict(role_counts)}")
    print(f"Warning cards: {len(warning_cards)}")
    print(f"Failures: {len(failures)}")

    if missing:
        print()
        print("Missing:")
        for player_id in missing[:50]:
            player = expected_ids[player_id]
            print(player_id, player.get("playerName"), player.get("role"), player.get("team"))

    if extra:
        print()
        print("Extra parsed ids:")
        print(extra[:50])

    if warning_cards:
        print()
        print("Warnings:")
        for player_id, warnings in warning_cards[:50]:
            print(player_id, warnings)

    if failures:
        print()
        print("Failures:")
        for failure in failures[:100]:
            print(failure)

    print("-" * 72)

    if (
        len(expected_ids) == 721
        and len(parsed_ids) == 721
        and not missing
        and not extra
        and not warning_cards
        and not failures
        and role_counts.get("hitter") == 442
        and role_counts.get("pitcher") == 279
        and status_counts.get(EXPECTED_CAPTURE_STATUS) == 721
    ):
        print("FULL PARSER CORPUS VERIFIED")
    else:
        print("FULL PARSER CORPUS NOT VERIFIED")
        raise SystemExit(1)

    print("=" * 72)


if __name__ == "__main__":
    main()
