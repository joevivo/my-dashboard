import json
from pathlib import Path

IN_FILE = Path("data/baseball/parsed/strat365/1980/ballparks/ballparks_v0.json")

EXPECTED_COUNT = 26
MIN_FACTOR = 1
MAX_FACTOR = 20


def fail(message: str):
    raise SystemExit(f"FAIL: {message}")


def main():
    if not IN_FILE.exists():
        fail(f"Missing input file: {IN_FILE}")

    data = json.loads(IN_FILE.read_text(encoding="utf-8"))
    parks = data.get("ballparks", [])

    if data.get("provider") != "strat365":
        fail("provider is not strat365")

    if data.get("season") != 1980:
        fail("season is not 1980")

    if data.get("ballparkCount") != len(parks):
        fail("ballparkCount does not match ballparks length")

    if len(parks) != EXPECTED_COUNT:
        fail(f"Expected {EXPECTED_COUNT} ballparks, found {len(parks)}")

    ids = [p.get("ballparkId") for p in parks]
    names = [p.get("ballparkName") for p in parks]

    if any(x is None for x in ids):
        fail("One or more ballpark IDs are missing")

    if len(ids) != len(set(ids)):
        fail("Duplicate ballpark IDs found")

    if len(names) != len(set(names)):
        fail("Duplicate ballpark names found")

    factor_fields = [
        "singleFactorLeft",
        "singleFactorRight",
        "homeRunFactorLeft",
        "homeRunFactorRight",
    ]

    for park in parks:
        if not park.get("ballparkName"):
            fail("Missing ballparkName")

        if not isinstance(park.get("capacity"), int) or park["capacity"] <= 0:
            fail(f"Bad capacity for {park.get('ballparkName')}")

        for field in factor_fields:
            value = park.get(field)
            if not isinstance(value, int):
                fail(f"{field} is not an int for {park.get('ballparkName')}")
            if value < MIN_FACTOR or value > MAX_FACTOR:
                fail(f"{field} out of range for {park.get('ballparkName')}: {value}")

    print("PASS: ballparks_v0 verification")
    print(f"Ballparks: {len(parks)}")

    for field in factor_fields:
        values = [p[field] for p in parks]
        print(f"{field}: min={min(values)} max={max(values)} avg={sum(values)/len(values):.2f}")


if __name__ == "__main__":
    main()
