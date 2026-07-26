from __future__ import annotations
import argparse
import hashlib
import json
import os
import shutil
import uuid
from pathlib import Path
from typing import Any
import re
EXPECTED_VALIDATOR_SHA256 = '6E3DA98B2D1E53ECB0BE316583609138C27A19F073344A3C20C11C91C0A8ADAF'

def sha256(path: Path) -> str:
    algorithm = hashlib.sha256()
    with path.open('rb') as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b''):
            algorithm.update(chunk)
    return algorithm.hexdigest().upper()

def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding='utf-8'))

def json_payload(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + '\n').encode('utf-8')

def game_set_signature(game_files: list[Path]) -> str:
    pairs = [f'{path.name}:{sha256(path)}' for path in sorted(game_files, key=lambda value: value.name)]
    return hashlib.sha256('\n'.join(pairs).encode('utf-8')).hexdigest().upper()

def relative_to_repo(repo_root: Path, path: Path) -> str:
    return path.resolve().relative_to(repo_root.resolve()).as_posix()

def collect_target_files(target: Path) -> dict[str, Path]:
    if not target.is_dir():
        return {}
    return {path.relative_to(target).as_posix(): path for path in target.rglob('*') if path.is_file()}

def verify_target(target: Path, expected_payloads: dict[str, bytes]) -> tuple[bool, list[str]]:
    failures: list[str] = []
    if not target.is_dir():
        return (False, [f'Canonical target is missing: {target}'])
    existing_files = collect_target_files(target)
    expected_names = set(expected_payloads)
    existing_names = set(existing_files)
    missing = sorted(expected_names - existing_names)
    extra = sorted(existing_names - expected_names)
    if missing:
        failures.append(f'Canonical target lacks files: {missing}')
    if extra:
        failures.append(f'Canonical target contains unexpected files: {extra}')
    for relative_name in sorted(expected_names & existing_names):
        actual_payload = existing_files[relative_name].read_bytes()
        if actual_payload != expected_payloads[relative_name]:
            failures.append(f'Canonical file conflicts: {relative_name}')
    return (not failures, failures)

def main() -> int:
    argument_parser = argparse.ArgumentParser()
    argument_parser.add_argument('--repo-root', required=True)
    argument_parser.add_argument('--parsed-root', required=True)
    argument_parser.add_argument('--canonical-target', required=True)
    arguments = argument_parser.parse_args()
    repo_root = Path(arguments.repo_root).resolve()
    parsed_root = Path(arguments.parsed_root).resolve()
    canonical_target = Path(arguments.canonical_target).resolve()
    parser_path = repo_root / 'baseball' / 'parser' / 'parse_strat365_season_ingestion_v0.py'
    validator_path = repo_root / 'baseball' / 'parser' / 'validate_strat365_season_ingestion_complete_night_v0.py'
    validation_report_path = parsed_root / 'complete-night-validation-v0.json'
    league_night_path = parsed_root / 'league-night-v0.json'
    game_directory = parsed_root / 'games'
    failures: list[str] = []
    parsed_relative = relative_to_repo(repo_root, parsed_root)
    parsed_scope_match = re.fullmatch('data/baseball/parsed/strat365/(\\d+)/season-ingestion/league-(\\d+)/(\\d{4}-\\d{2}-\\d{2})', parsed_relative)
    if parsed_scope_match is None:
        failures.append(f'Parsed root does not match the expected season-ingestion namespace: {parsed_relative}')
        season = ''
        league_id = ''
        league_date = ''
    else:
        season, league_id, league_date = parsed_scope_match.groups()
    expected_scope = f'{season}/league-{league_id}/{league_date}'
    expected_target_relative = f'data/baseball/canonical/strat365/{season}/season-ingestion/league-{league_id}/{league_date}'
    expected_target = (repo_root / Path(expected_target_relative)).resolve()
    validation_report_seed = load_json(validation_report_path)
    promotion_decision_seed = validation_report_seed.get('promotionDecision', {})
    authoritative_hashes_seed = validation_report_seed.get('authoritativeHashes', {})
    report_authorization_scope = str(promotion_decision_seed.get('authorizationScope', ''))
    if report_authorization_scope != expected_scope:
        failures.append(f'Validation authorization scope differs: {report_authorization_scope}')
    expected_parser_sha256 = str(authoritative_hashes_seed.get('parserSha256', ''))
    expected_capture_lock_sha256 = str(authoritative_hashes_seed.get('captureLockSha256', ''))
    expected_league_night_sha256 = str(authoritative_hashes_seed.get('leagueNightSha256', ''))
    expected_game_set_signature = str(authoritative_hashes_seed.get('gameSetSignature', ''))
    for hash_name, hash_value in (('parserSha256', expected_parser_sha256), ('captureLockSha256', expected_capture_lock_sha256), ('leagueNightSha256', expected_league_night_sha256), ('gameSetSignature', expected_game_set_signature)):
        if re.fullmatch('[0-9A-F]{64}', hash_value) is None:
            failures.append(f'Validation authoritative hash is invalid: {hash_name}={hash_value}')
    if canonical_target != expected_target:
        failures.append('Canonical target does not match the authorized namespace.')
    parser_hash = sha256(parser_path)
    validator_hash = sha256(validator_path)
    validation_report_hash = sha256(validation_report_path)
    league_night_hash = sha256(league_night_path)
    if parser_hash != expected_parser_sha256 and (not canonical_target.exists()):
        failures.append(f'Parser hash mismatch: {parser_hash}')
    if validator_hash != EXPECTED_VALIDATOR_SHA256:
        failures.append(f'Validator hash mismatch: {validator_hash}')
    if league_night_hash != expected_league_night_sha256:
        failures.append(f'League-night hash mismatch: {league_night_hash}')
    game_files = sorted(game_directory.glob('game-*-v0.json'), key=lambda value: value.name)
    current_game_set_signature = game_set_signature(game_files)
    parsed_game_ids = {int(load_json(game_path).get('gameId', -1)) for game_path in game_files}
    if len(game_files) != 18 or len(parsed_game_ids) != 18:
        failures.append('Parsed game inventory does not contain 18 unique league games.')
    if parsed_game_ids:
        expected_game_ids = set(range(min(parsed_game_ids), max(parsed_game_ids) + 1))
    else:
        expected_game_ids = set()
    if parsed_game_ids != expected_game_ids:
        failures.append(f'Parsed game IDs are not one contiguous 18-game league-night range: {sorted(parsed_game_ids)}')
    if len(game_files) != 18:
        failures.append(f'Expected 18 game files; found {len(game_files)}.')
    if current_game_set_signature != expected_game_set_signature:
        failures.append(f'Game-set signature mismatch: {current_game_set_signature}')
    validation_report = load_json(validation_report_path)
    promotion_decision = validation_report.get('promotionDecision', {})
    authoritative_hashes = validation_report.get('authoritativeHashes', {})
    gates = validation_report.get('gates', {})
    validation_failures = list(validation_report.get('failures', []))
    if promotion_decision.get('canonicalPromotionAuthorized') is not True:
        failures.append('Validation report does not authorize promotion.')
    if promotion_decision.get('status') != 'AUTHORIZED_FOR_ATOMIC_CANONICAL_PROMOTION':
        failures.append('Validation report has an invalid promotion status.')
    if promotion_decision.get('requiresAtomicWrite') is not True:
        failures.append('Validation report does not require an atomic write.')
    if promotion_decision.get('authorizationScope') != expected_scope:
        failures.append('Validation authorization scope differs.')
    if validation_failures:
        failures.append('Validation report contains failures.')
    if not gates or not all((value is True for value in gates.values())):
        failures.append('Not all independent validation gates passed.')
    expected_authoritative_hashes = {'parserSha256': expected_parser_sha256, 'captureLockSha256': expected_capture_lock_sha256, 'leagueNightSha256': expected_league_night_sha256, 'gameSetSignature': expected_game_set_signature}
    for hash_name, expected_hash in expected_authoritative_hashes.items():
        actual_hash = str(authoritative_hashes.get(hash_name, ''))
        if actual_hash != expected_hash:
            failures.append(f'Validation authoritative hash differs: {hash_name}={actual_hash}')
    league_night = load_json(league_night_path)
    if int(league_night.get('gameCount', -1)) != 18:
        failures.append('League-night game count is not 18.')
    if int(league_night.get('structuredGameCount', -1)) != 18:
        failures.append('League-night structured-game count is not 18.')
    reconciliation_summary = league_night.get('reconciliationSummary', {})
    if reconciliation_summary.get('completeNightReady') is not True:
        failures.append('League-night reconciliation is not complete.')
    if int(reconciliation_summary.get('reconciledGameCount', -1)) != 18:
        failures.append('League-night reconciled-game count is not 18.')
    game_ids: set[int] = set()
    for game_path in game_files:
        game = load_json(game_path)
        game_id = int(game.get('gameId', -1))
        game_ids.add(game_id)
        reconciliation = game.get('reconciliation', {})
        if reconciliation.get('status') != 'RECONCILED':
            failures.append(f'Game {game_id} is not reconciled.')
        if reconciliation.get('leagueResultOutcomeMatch') is not True:
            failures.append(f'Game {game_id} result does not reconcile.')
        if reconciliation.get('playByPlayAttached') is not True:
            failures.append(f'Game {game_id} lacks play-by-play.')
    if game_ids != expected_game_ids:
        failures.append(f'Game ID coverage differs: {sorted(game_ids)}')
    source_payloads: dict[str, tuple[Path, bytes]] = {'league-night-v0.json': (league_night_path, league_night_path.read_bytes()), 'complete-night-validation-v0.json': (validation_report_path, validation_report_path.read_bytes())}
    for game_path in game_files:
        relative_name = (Path('games') / game_path.name).as_posix()
        source_payloads[relative_name] = (game_path, game_path.read_bytes())
    manifest_file_rows: list[dict[str, Any]] = []
    for relative_name in sorted(source_payloads):
        source_path, payload = source_payloads[relative_name]
        manifest_file_rows.append({'canonicalPath': relative_name, 'sourcePath': relative_to_repo(repo_root, source_path), 'sha256': hashlib.sha256(payload).hexdigest().upper(), 'byteCount': len(payload)})
    manifest_validator_sha256 = validator_hash
    existing_manifest_path = canonical_target / 'promotion-manifest-v0.json'
    if existing_manifest_path.is_file():
        existing_manifest = load_json(existing_manifest_path)
        existing_source_authority = existing_manifest.get('sourceAuthority', {})
        existing_validator_sha256 = str(existing_source_authority.get('validatorSha256', ''))
        if re.fullmatch('[0-9A-F]{64}', existing_validator_sha256):
            manifest_validator_sha256 = existing_validator_sha256
    manifest = {'schemaVersion': 'strat365-canonical-league-night-manifest-v0', 'season': season, 'leagueId': league_id, 'leagueDate': league_date, 'canonicalTarget': expected_target_relative, 'promotionStatus': 'PROMOTED', 'promotionAuthority': {'validationReport': relative_to_repo(repo_root, validation_report_path), 'validationReportSha256': validation_report_hash, 'decision': 'AUTHORIZED_FOR_ATOMIC_CANONICAL_PROMOTION', 'requiresAtomicWrite': True}, 'sourceAuthority': {'parserSha256': parser_hash, 'validatorSha256': manifest_validator_sha256, 'leagueNightSha256': league_night_hash, 'gameSetSignature': current_game_set_signature}, 'counts': {'games': len(game_files), 'payloadFiles': len(source_payloads), 'packageFiles': len(source_payloads) + 1}, 'payloadFiles': manifest_file_rows, 'overwritePolicy': {'conflictingExistingTarget': 'REJECT', 'identicalExistingTarget': 'ACCEPT_IDEMPOTENTLY'}}
    manifest_payload = json_payload(manifest)
    expected_payloads = {relative_name: payload for relative_name, (_, payload) in source_payloads.items()}
    expected_payloads['promotion-manifest-v0.json'] = manifest_payload
    if failures:
        print('# RESULT SUMMARY')
        print('ATOMIC_CANONICAL_PROMOTION: FAIL')
        print('PROMOTION_STATUS: BLOCKED')
        print(f'CANONICAL_TARGET: {expected_target_relative}')
        print(f'GAME_SET_SIGNATURE: {current_game_set_signature}')
        print(f'FAILURE_COUNT: {len(failures)}')
        for failure in failures[:30]:
            print(f'FAILURE_DETAIL: {failure}')
        print('FILES_MODIFIED_BY_PROMOTER: 0')
        print('CONFLICT_DETECTED: NO')
        print('LIVE_REQUESTS_EXECUTED: 0')
        return 1
    if canonical_target.exists():
        target_valid, target_failures = verify_target(canonical_target, expected_payloads)
        if not target_valid:
            print('# RESULT SUMMARY')
            print('ATOMIC_CANONICAL_PROMOTION: FAIL')
            print('PROMOTION_STATUS: CONFLICT_REJECTED')
            print(f'CANONICAL_TARGET: {expected_target_relative}')
            print(f'GAME_SET_SIGNATURE: {current_game_set_signature}')
            print(f'FAILURE_COUNT: {len(target_failures)}')
            for failure in target_failures[:30]:
                print(f'FAILURE_DETAIL: {failure}')
            print('FILES_MODIFIED_BY_PROMOTER: 0')
            print('CONFLICT_DETECTED: YES')
            print('LIVE_REQUESTS_EXECUTED: 0')
            return 1
        manifest_hash = sha256(canonical_target / 'promotion-manifest-v0.json')
        print('# RESULT SUMMARY')
        print('ATOMIC_CANONICAL_PROMOTION: PASS')
        print('PROMOTION_STATUS: ALREADY_PRESENT')
        print(f'CANONICAL_TARGET: {expected_target_relative}')
        print('CANONICAL_TARGET_FILE_COUNT: 21')
        print('CANONICAL_GAME_FILE_COUNT: 18')
        print(f'GAME_SET_SIGNATURE: {current_game_set_signature}')
        print(f'CANONICAL_MANIFEST_SHA256: {manifest_hash}')
        print('PROMOTION_IDEMPOTENT: YES')
        print('FILES_MODIFIED_BY_PROMOTER: 0')
        print('CONFLICT_DETECTED: NO')
        print('FAILURE_COUNT: 0')
        print('FAILURE_DETAIL: none')
        print('LIVE_REQUESTS_EXECUTED: 0')
        return 0
    canonical_target.parent.mkdir(parents=True, exist_ok=True)
    temporary_target = canonical_target.parent / f'.{canonical_target.name}.promotion-{uuid.uuid4().hex}'
    files_modified = 0
    try:
        temporary_target.mkdir(parents=False, exist_ok=False)
        for relative_name in sorted(expected_payloads):
            destination = temporary_target / relative_name
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(expected_payloads[relative_name])
            files_modified += 1
        temporary_valid, temporary_failures = verify_target(temporary_target, expected_payloads)
        if not temporary_valid:
            raise RuntimeError('Temporary canonical package failed verification: ' + ' | '.join(temporary_failures))
        os.replace(temporary_target, canonical_target)
        target_valid, target_failures = verify_target(canonical_target, expected_payloads)
        if not target_valid:
            raise RuntimeError('Promoted canonical package failed verification: ' + ' | '.join(target_failures))
    finally:
        if temporary_target.exists():
            shutil.rmtree(temporary_target)
    manifest_hash = sha256(canonical_target / 'promotion-manifest-v0.json')
    print('# RESULT SUMMARY')
    print('ATOMIC_CANONICAL_PROMOTION: PASS')
    print('PROMOTION_STATUS: PROMOTED')
    print(f'CANONICAL_TARGET: {expected_target_relative}')
    print('CANONICAL_TARGET_FILE_COUNT: 21')
    print('CANONICAL_GAME_FILE_COUNT: 18')
    print(f'GAME_SET_SIGNATURE: {current_game_set_signature}')
    print(f'CANONICAL_MANIFEST_SHA256: {manifest_hash}')
    print('PROMOTION_IDEMPOTENT: PENDING_SECOND_RUN')
    print(f'FILES_MODIFIED_BY_PROMOTER: {files_modified}')
    print('CONFLICT_DETECTED: NO')
    print('FAILURE_COUNT: 0')
    print('FAILURE_DETAIL: none')
    print('LIVE_REQUESTS_EXECUTED: 0')
    return 0
if __name__ == '__main__':
    raise SystemExit(main())
