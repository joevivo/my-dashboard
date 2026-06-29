import json
import re
from datetime import datetime, timezone
from html import unescape
from pathlib import Path

PROVIDER = "strat365"
SEASON = 1980
PARSER_VERSION = "ballparks_v0"

RAW_HTML = Path("data/baseball/raw/strat365/1980/ballparks/index.html")
OUT_DIR = Path("data/baseball/parsed/strat365/1980/ballparks")
OUT_FILE = OUT_DIR / "ballparks_v0.json"

SOURCE_URL = "https://365.strat-o-matic.com/playerset/browse/ballparks/1980"


def clean_text(value: str) -> str:
    value = re.sub(r"<[^>]+>", " ", value)
    value = unescape(value)
    value = re.sub(r"\s+", " ", value).strip()
    return value


def to_int(value: str):
    value = value.replace(",", "").strip()
    return int(value) if value else None


def parse_ballparks(html: str):
    tbody_match = re.search(r"<tbody>(.*?)</tbody>", html, flags=re.I | re.S)
    if not tbody_match:
        raise RuntimeError("Could not find ballpark table tbody.")

    tbody = tbody_match.group(1)
    rows = re.findall(r"<tr[^>]*>(.*?)</tr>", tbody, flags=re.I | re.S)

    ballparks = []

    for row in rows:
        cells = re.findall(r"<td[^>]*>(.*?)</td>", row, flags=re.I | re.S)
        if len(cells) < 6:
            continue

        name_cell = cells[0]
        id_match = re.search(r"/ballpark/(\d+)", name_cell)
        ballpark_id = int(id_match.group(1)) if id_match else None

        name = clean_text(name_cell)
        capacity = to_int(clean_text(cells[1]))
        si_l = to_int(clean_text(cells[2]))
        si_r = to_int(clean_text(cells[3]))
        hr_l = to_int(clean_text(cells[4]))
        hr_r = to_int(clean_text(cells[5]))

        ballparks.append({
            "provider": PROVIDER,
            "season": SEASON,
            "ballparkId": ballpark_id,
            "ballparkName": name,
            "capacity": capacity,
            "singleFactorLeft": si_l,
            "singleFactorRight": si_r,
            "homeRunFactorLeft": hr_l,
            "homeRunFactorRight": hr_r,
        })

    return ballparks


def main():
    html = RAW_HTML.read_text(encoding="utf-8")
    ballparks = parse_ballparks(html)

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    payload = {
        "provider": PROVIDER,
        "season": SEASON,
        "parserVersion": PARSER_VERSION,
        "sourceUrl": SOURCE_URL,
        "sourceHtmlFile": str(RAW_HTML),
        "parsedAt": datetime.now(timezone.utc).isoformat(),
        "ballparkCount": len(ballparks),
        "ballparks": ballparks,
    }

    OUT_FILE.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    print(f"Saved {OUT_FILE}")
    print(f"Ballparks: {len(ballparks)}")
    for park in ballparks[:10]:
        print(
            f"- {park['ballparkName']}: "
            f"SI L/R {park['singleFactorLeft']}/{park['singleFactorRight']} | "
            f"HR L/R {park['homeRunFactorLeft']}/{park['homeRunFactorRight']}"
        )


if __name__ == "__main__":
    main()
