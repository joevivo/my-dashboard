from pathlib import Path
import json
from collections import Counter

universe_path = Path("data/baseball/raw/strat365/1980/players/1980_players_universe.json")
cards_dir = Path("data/baseball/raw/strat365/authenticated/1980/cards")

print("BIE Authenticated Capture Inventory Verification")
print("=" * 72)

universe = json.loads(universe_path.read_text(encoding="utf-8", errors="replace"))
players = universe.get("players", [])

expected_ids = {str(p["playerId"]): p for p in players}

html_files = {p.stem: p for p in cards_dir.glob("*.html")}
meta_files = {}

invalid_meta = []
status_counts = Counter()
role_counts = Counter()

for path in cards_dir.glob("*.capture.json"):
    player_id = path.name.replace(".capture.json", "")
    try:
        data = json.loads(path.read_text(encoding="utf-8", errors="replace"))
    except Exception as exc:
        invalid_meta.append((player_id, f"json_error: {exc}"))
        continue

    meta_files[player_id] = path
    status = data.get("status")
    role = data.get("role") or data.get("validationRole") or "unknown"

    status_counts[status] += 1
    role_counts[role] += 1

    if status != "validated_authenticated_card":
        invalid_meta.append((player_id, f"status={status}"))

missing_html = sorted(set(expected_ids) - set(html_files), key=int)
missing_meta = sorted(set(expected_ids) - set(meta_files), key=int)
extra_html = sorted(set(html_files) - set(expected_ids), key=int)
extra_meta = sorted(set(meta_files) - set(expected_ids), key=int)

print(f"Universe players: {len(expected_ids)}")
print(f"Universe role counts: {universe.get('roleCounts')}")
print(f"HTML files matching folder: {len(html_files)}")
print(f"Metadata files matching folder: {len(meta_files)}")
print(f"Validated metadata statuses: {status_counts.get('validated_authenticated_card', 0)}")
print(f"Metadata status counts: {dict(status_counts)}")
print(f"Metadata role counts: {dict(role_counts)}")
print()

if missing_html:
    print("Missing HTML:")
    for player_id in missing_html:
        p = expected_ids[player_id]
        print(player_id, p.get("playerName"), p.get("role"), p.get("team"))

if missing_meta:
    print("Missing metadata:")
    for player_id in missing_meta:
        p = expected_ids[player_id]
        print(player_id, p.get("playerName"), p.get("role"), p.get("team"))

if extra_html:
    print("Extra HTML ids:", extra_html)

if extra_meta:
    print("Extra metadata ids:", extra_meta)

if invalid_meta:
    print("Invalid metadata:")
    for player_id, reason in invalid_meta:
        p = expected_ids.get(player_id, {})
        print(player_id, p.get("playerName"), p.get("role"), reason)

print()

if (
    len(expected_ids) == 721
    and len(html_files) == 721
    and len(meta_files) == 721
    and not missing_html
    and not missing_meta
    and not extra_html
    and not extra_meta
    and not invalid_meta
    and status_counts.get("validated_authenticated_card", 0) == 721
):
    print("FULL AUTHENTICATED CAPTURE VALIDATED")
else:
    print("FULL AUTHENTICATED CAPTURE NOT COMPLETE")

print("=" * 72)
