from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import subprocess
import sys
import tempfile
import unittest


def write_json(path: pathlib.Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            value,
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
        newline="\n",
    )


def sha256(path: pathlib.Path) -> str:
    return hashlib.sha256(
        path.read_bytes()
    ).hexdigest().upper()


def tree_hash(root: pathlib.Path) -> str:
    rows: list[str] = []

    for path in sorted(
        item
        for item in root.rglob("*")
        if item.is_file()
    ):
        rows.append(
            f"{path.relative_to(root).as_posix()}|"
            f"{path.stat().st_size}|{sha256(path)}"
        )

    return hashlib.sha256(
        ("\n".join(rows) + "\n").encode("utf-8")
    ).hexdigest().upper()


class TeamNightPromoterTests(unittest.TestCase):
    promoter: pathlib.Path

    def build_fixture(
        self,
        temporary_root: pathlib.Path,
    ) -> tuple[
        pathlib.Path,
        pathlib.Path,
        pathlib.Path,
        str,
    ]:
        repo = temporary_root / "repo"

        parser_path = (
            repo
            / "baseball/parser/"
            / "parse_strat365_season_ingestion_v0.py"
        )
        validator_path = (
            repo
            / "baseball/parser/"
            / "validate_strat365_season_ingestion_complete_night_v0.py"
        )

        parser_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        parser_path.write_text(
            "PARSER_FIXTURE = True\n",
            encoding="utf-8",
            newline="\n",
        )

        validator_path.write_text(
            "VALIDATOR_FIXTURE = True\n",
            encoding="utf-8",
            newline="\n",
        )

        capture = (
            repo
            / "data/baseball/raw/strat365/1968/"
            / "season-ingestion/league-479431/"
            / "2026-08-03/capture-fixture"
        )
        capture.mkdir(parents=True)

        capture_lock = (
            capture
            / "capture-lock-and-promotion-decision-v1.json"
        )
        plan = capture / "game-capture-plan.json"
        run_manifest = capture / "run-manifest.json"

        write_json(capture_lock, {"fixture": "lock"})
        write_json(plan, {"fixture": "plan"})
        write_json(run_manifest, {"fixture": "manifest"})

        parsed = (
            repo
            / "data/baseball/parsed/strat365/1968/"
            / "season-ingestion/league-479431/"
            / "2026-08-03"
        )
        games = parsed / "games"
        games.mkdir(parents=True)

        for game_id in (78, 84, 90):
            write_json(
                games / f"game-{game_id}-v0.json",
                {
                    "schemaVersion": "strat365-game-v0",
                    "gameId": game_id,
                    "homeTeam": {
                        "name": "Aquarium Drinkers",
                    },
                    "awayTeam": {
                        "name": "Fixture Opponent",
                    },
                    "reconciliation": {
                        "resultSourceMatch": True,
                        "playByPlayAttached": True,
                    },
                },
            )

        league_night = parsed / "league-night-v0.json"

        write_json(
            league_night,
            {
                "schemaVersion": "strat365-league-night-v0",
                "leagueId": "479431",
                "leagueDate": "2026-08-03",
                "gameCount": 3,
                "structuredGameCount": 3,
                "reconciliationSummary": {
                    "reconciledGameCount": 3,
                },
            },
        )

        game_files = sorted(
            games.glob("game-*-v0.json")
        )

        game_signature = hashlib.sha256(
            "\n".join(
                f"{path.name}:{sha256(path)}"
                for path in game_files
            ).encode("utf-8")
        ).hexdigest().upper()

        parsed_relative = (
            "data/baseball/parsed/strat365/1968/"
            "season-ingestion/league-479431/"
            "2026-08-03"
        )
        capture_relative = (
            "data/baseball/raw/strat365/1968/"
            "season-ingestion/league-479431/"
            "2026-08-03/capture-fixture"
        )

        report = {
            "schemaVersion": (
                "strat365-complete-night-validation-v0"
            ),
            "season": "1968",
            "leagueId": "479431",
            "leagueDate": "2026-08-03",
            "scope": {
                "scopeType": "TEAM_NIGHT",
                "teamId": "1853975",
                "teamName": "Aquarium Drinkers",
                "parsedRoot": parsed_relative,
                "leagueNightFile": (
                    parsed_relative
                    + "/league-night-v0.json"
                ),
                "gameDirectory": (
                    parsed_relative + "/games"
                ),
                "captureDirectory": capture_relative,
            },
            "authoritativeHashes": {
                "parserSha256": sha256(parser_path),
                "captureLockSha256": sha256(
                    capture_lock
                ),
                "planSha256": sha256(plan),
                "manifestSha256": sha256(
                    run_manifest
                ),
                "leagueNightSha256": sha256(
                    league_night
                ),
                "gameSetSignature": game_signature,
            },
            "counts": {
                "gameFiles": 3,
                "reconciledGames": 3,
            },
            "gates": {
                f"gate{index:02d}": True
                for index in range(1, 18)
            },
            "promotionDecision": {
                "scopeType": "TEAM_NIGHT",
                "status": (
                    "AUTHORIZED_FOR_ATOMIC_CANONICAL_PROMOTION"
                ),
                "canonicalPromotionAuthorized": True,
                "authorizationScope": (
                    "1968/league-479431/"
                    "team-1853975/2026-08-03"
                ),
                "requiresAtomicWrite": True,
                "liveRecaptureAuthorized": False,
                "sourceStagingMutationAuthorized": False,
            },
            "failures": [],
        }

        write_json(
            parsed
            / "complete-night-validation-v0.json",
            report,
        )

        target = (
            repo
            / "data/baseball/canonical/strat365/1968/"
            / "season-ingestion/league-479431/"
            / "team-1853975/2026-08-03"
        )

        return repo, parsed, target, tree_hash(parsed)

    def execute(
        self,
        repo: pathlib.Path,
        parsed: pathlib.Path,
        target: pathlib.Path,
        team_id: str = "1853975",
    ) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [
                sys.executable,
                "-B",
                str(self.promoter),
                "--repo-root",
                str(repo),
                "--parsed-root",
                str(parsed),
                "--team-id",
                team_id,
                "--canonical-target",
                str(target),
            ],
            text=True,
            capture_output=True,
            check=False,
        )

    def test_success_and_idempotence(self) -> None:
        with tempfile.TemporaryDirectory() as value:
            repo, parsed, target, source_hash = (
                self.build_fixture(pathlib.Path(value))
            )

            first = self.execute(
                repo,
                parsed,
                target,
            )

            self.assertEqual(
                first.returncode,
                0,
                first.stdout + first.stderr,
            )
            self.assertIn(
                "PROMOTION_STATUS: PROMOTED",
                first.stdout,
            )
            self.assertEqual(
                len(
                    [
                        path
                        for path in target.rglob("*")
                        if path.is_file()
                    ]
                ),
                6,
            )
            self.assertEqual(
                tree_hash(parsed),
                source_hash,
            )
            self.assertEqual(
                list(
                    target.parent.glob(
                        f".{target.name}.promotion-*"
                    )
                ),
                [],
            )

            second = self.execute(
                repo,
                parsed,
                target,
            )

            self.assertEqual(
                second.returncode,
                0,
                second.stdout + second.stderr,
            )
            self.assertIn(
                "PROMOTION_STATUS: ALREADY_PRESENT",
                second.stdout,
            )
            self.assertIn(
                "PROMOTION_IDEMPOTENT: YES",
                second.stdout,
            )
            self.assertEqual(
                tree_hash(parsed),
                source_hash,
            )

    def test_wrong_team_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as value:
            repo, parsed, target, source_hash = (
                self.build_fixture(pathlib.Path(value))
            )

            wrong_target = (
                target.parent.parent
                / "team-9999999"
                / target.name
            )

            result = self.execute(
                repo,
                parsed,
                wrong_target,
                team_id="9999999",
            )

            self.assertNotEqual(result.returncode, 0)
            self.assertIn(
                "PROMOTION_STATUS: BLOCKED",
                result.stdout,
            )
            self.assertFalse(wrong_target.exists())
            self.assertEqual(
                tree_hash(parsed),
                source_hash,
            )

    def test_wrong_namespace_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as value:
            repo, parsed, _, source_hash = (
                self.build_fixture(pathlib.Path(value))
            )

            wrong_target = (
                repo
                / "data/baseball/canonical/wrong-target"
            )

            result = self.execute(
                repo,
                parsed,
                wrong_target,
            )

            self.assertNotEqual(result.returncode, 0)
            self.assertIn(
                "PROMOTION_STATUS: BLOCKED",
                result.stdout,
            )
            self.assertFalse(wrong_target.exists())
            self.assertEqual(
                tree_hash(parsed),
                source_hash,
            )

    def test_conflicting_target_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as value:
            repo, parsed, target, source_hash = (
                self.build_fixture(pathlib.Path(value))
            )

            first = self.execute(
                repo,
                parsed,
                target,
            )

            self.assertEqual(
                first.returncode,
                0,
                first.stdout + first.stderr,
            )

            (
                target / "league-night-v0.json"
            ).write_text(
                '{"conflict":true}\n',
                encoding="utf-8",
                newline="\n",
            )

            second = self.execute(
                repo,
                parsed,
                target,
            )

            self.assertNotEqual(second.returncode, 0)
            self.assertIn(
                "PROMOTION_STATUS: CONFLICT_REJECTED",
                second.stdout,
            )
            self.assertIn(
                "CONFLICT_DETECTED: YES",
                second.stdout,
            )
            self.assertEqual(
                tree_hash(parsed),
                source_hash,
            )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--promoter", required=True)
    arguments = parser.parse_args()

    TeamNightPromoterTests.promoter = (
        pathlib.Path(arguments.promoter).resolve()
    )

    suite = (
        unittest.defaultTestLoader.loadTestsFromTestCase(
            TeamNightPromoterTests
        )
    )

    result = unittest.TextTestRunner(
        stream=sys.stdout,
        verbosity=1,
    ).run(suite)

    print("# RESULT SUMMARY")
    print(
        "TEAM_NIGHT_PROMOTER_FIXTURE_TESTS: "
        + (
            "PASS"
            if result.wasSuccessful()
            else "FAIL"
        )
    )
    print(f"TESTS_RUN: {result.testsRun}")
    print(
        f"TEST_FAILURE_COUNT: "
        f"{len(result.failures)}"
    )
    print(
        f"TEST_ERROR_COUNT: "
        f"{len(result.errors)}"
    )
    print("REPOSITORY_CANONICAL_WRITES: 0")
    print("LIVE_REQUESTS_EXECUTED: 0")

    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    sys.exit(main())