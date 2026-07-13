
import csv
import json
from pathlib import Path

SEASON = "1968"
BASE = Path("data/baseball/parsed/strat365") / SEASON
OUT_DIR = BASE / "card-coverage"
OUT_DIR.mkdir(parents=True, exist_ok=True)

FULL_CSV = OUT_DIR / "1968.card-coverage-manifest-v0.csv"
FULL_JSON = OUT_DIR / "1968.card-coverage-manifest-v0.json"
MISSING_CSV = OUT_DIR / "1968.missing-card-evidence-manifest-v0.csv"
MISSING_JSON = OUT_DIR / "1968.missing-card-evidence-manifest-v0.json"

def load_json(path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None

def records_from(obj):
    if obj is None:
        return []
    if isinstance(obj, list):
        return obj
    if isinstance(obj, dict):
        for key in ("players", "rows", "records", "items"):
            value = obj.get(key)
            if isinstance(value, list):
                return value
        if obj.get("playerId") or obj.get("playerName"):
            return [obj]
    return []

def first_present(row, names):
    for name in names:
        if isinstance(row, dict) and row.get(name) not in (None, ""):
            return row.get(name)
    return ""

def salary_to_millions(value):
    if value in (None, ""):
        return ""
    if isinstance(value, dict):
        for key in ("millions", "raw", "dollars"):
            if value.get(key) not in (None, ""):
                if key == "dollars":
                    try:
                        return round(float(value[key]) / 1000000.0, 3)
                    except Exception:
                        return ""
                return salary_to_millions(value[key])
        return ""
    text = str(value).replace("$", "").replace("M", "").strip()
    try:
        return float(text)
    except Exception:
        return ""

def collect_players():
    players = {}
    for path in BASE.rglob("*.json"):
        text = str(path)
        if any(part in text for part in ("\\cards\\", "\\card-probability-summaries\\", "\\card-mechanics\\", "\\draft-prep\\", "\\card-coverage\\")):
            continue
        if not any(token in path.name for token in ("playerset", "roster", "draft", "metadata", "board", "signal")):
            continue
        for row in records_from(load_json(path)):
            if not isinstance(row, dict):
                continue
            player_id = str(first_present(row, ("playerId", "id"))).strip()
            if not player_id:
                continue
            if player_id not in players:
                players[player_id] = {
                    "playerId": player_id,
                    "playerName": first_present(row, ("playerName", "name")),
                    "team": first_present(row, ("team", "teamName")),
                    "role": first_present(row, ("role", "playerType")),
                    "salaryMillions": salary_to_millions(first_present(row, ("salaryMillions", "salary"))),
                    "browserEndurance": first_present(row, ("browserEndurance", "endurance", "pitcherEndurance", "enduranceText")),
                    "sourceFile": path.name,
                }
    return players

def collect_card_ids(folder, suffix):
    ids = set()
    folder_path = BASE / folder
    if not folder_path.exists():
        return ids
    for path in folder_path.glob(f"*{suffix}"):
        first = path.name.split(".", 1)[0]
        if first.isdigit():
            ids.add(first)
    return ids

players = collect_players()
card_ids = collect_card_ids("cards", ".parsed-card-evidence.json")
summary_ids = collect_card_ids("card-probability-summaries", ".card-probability-summary.json")

rows = []
for player_id, row in players.items():
    has_card = player_id in card_ids
    has_summary = player_id in summary_ids
    rows.append({
        **row,
        "hasParsedCard": has_card,
        "hasProbabilitySummary": has_summary,
        "probablePlayerUrl": f"https://365.strat-o-matic.com/player/{player_id}/1968/1/60",
    })

rows.sort(key=lambda r: (str(r.get("role", "")), str(r.get("playerName", ""))))
missing = [r for r in rows if not r["hasParsedCard"]]

fieldnames = ["playerId", "playerName", "team", "role", "salaryMillions", "browserEndurance", "hasParsedCard", "hasProbabilitySummary", "sourceFile", "probablePlayerUrl"]

for out_path, out_rows in ((FULL_CSV, rows), (MISSING_CSV, missing)):
    with out_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(out_rows)

FULL_JSON.write_text(json.dumps(rows, indent=2), encoding="utf-8")
MISSING_JSON.write_text(json.dumps(missing, indent=2), encoding="utf-8")

missing_hitters = [r for r in missing if r.get("role") == "hitter"]
missing_pitchers = [r for r in missing if r.get("role") == "pitcher"]
missing_starters = [r for r in missing_pitchers if str(r.get("browserEndurance", "")).startswith("S")]

cheap_missing_starters = []
for r in missing_starters:
    salary = r.get("salaryMillions")
    try:
        if salary != "" and float(salary) < 2.0:
            cheap_missing_starters.append(r)
    except Exception:
        pass

print("# RESULT SUMMARY")
print(f"TOTAL_PLAYERS: {len(rows)}")
print(f"PARSED_CARD_EVIDENCE: {len(card_ids)}")
print(f"PROBABILITY_SUMMARIES: {len(summary_ids)}")
print(f"MISSING_PARSED_CARD_EVIDENCE: {len(missing)}")
print(f"MISSING_HITTERS: {len(missing_hitters)}")
print(f"MISSING_PITCHERS: {len(missing_pitchers)}")
print(f"MISSING_STARTER_ENDURANCE_PITCHERS_WITH_SOURCE_FIELD: {len(missing_starters)}")
print(f"CHEAP_MISSING_STARTERS_UNDER_2M_WITH_SOURCE_FIELD: {len(cheap_missing_starters)}")
print(f"FULL_CSV: {FULL_CSV}")
print(f"MISSING_CSV: {MISSING_CSV}")
print("")
print("# CHEAP MISSING STARTER SAMPLE")
for r in cheap_missing_starters[:40]:
    print(f"{r['playerId']} | {r['playerName']} | {r['team']} | ${r['salaryMillions']}M | {r['browserEndurance']} | {r['probablePlayerUrl']}")

