import json
from pathlib import Path

IN_FILE = Path("data/baseball/parsed/strat365/1980/ballparks/ballparks_v0.json")

FACTOR_FIELDS = [
    ("singleFactorLeft", "SI L"),
    ("singleFactorRight", "SI R"),
    ("homeRunFactorLeft", "HR L"),
    ("homeRunFactorRight", "HR R"),
]


def avg(values):
    return sum(values) / len(values) if values else 0


def classify_park(park):
    si_avg = avg([park["singleFactorLeft"], park["singleFactorRight"]])
    hr_avg = avg([park["homeRunFactorLeft"], park["homeRunFactorRight"]])

    if si_avg >= 14 and hr_avg >= 14:
        return "run_amplifier"
    if si_avg <= 6 and hr_avg <= 6:
        return "run_suppressor"
    if hr_avg >= 14:
        return "power_amplifier"
    if hr_avg <= 6:
        return "power_suppressor"
    if si_avg >= 14:
        return "singles_amplifier"
    if si_avg <= 6:
        return "singles_suppressor"
    return "neutral_mixed"


def main():
    data = json.loads(IN_FILE.read_text(encoding="utf-8"))
    parks = data["ballparks"]

    print("# Ballpark Inventory v0")
    print()
    print(f"Ballparks: {len(parks)}")
    print()

    print("## Factor ranges")
    for field, label in FACTOR_FIELDS:
        values = [p[field] for p in parks]
        print(f"{label}: min={min(values)} max={max(values)} avg={avg(values):.2f}")

    print()
    print("## Buckets")
    buckets = {}
    for park in parks:
        bucket = classify_park(park)
        buckets.setdefault(bucket, []).append(park)

    for bucket in sorted(buckets):
        print(f"{bucket}: {len(buckets[bucket])}")

    print()
    print("## Highest HR parks")
    for park in sorted(parks, key=lambda p: (p["homeRunFactorLeft"] + p["homeRunFactorRight"], p["ballparkName"]), reverse=True)[:8]:
        print(
            f"- {park['ballparkName']}: "
            f"HR L/R {park['homeRunFactorLeft']}/{park['homeRunFactorRight']} | "
            f"SI L/R {park['singleFactorLeft']}/{park['singleFactorRight']} | "
            f"{classify_park(park)}"
        )

    print()
    print("## Lowest HR parks")
    for park in sorted(parks, key=lambda p: (p["homeRunFactorLeft"] + p["homeRunFactorRight"], p["ballparkName"]))[:8]:
        print(
            f"- {park['ballparkName']}: "
            f"HR L/R {park['homeRunFactorLeft']}/{park['homeRunFactorRight']} | "
            f"SI L/R {park['singleFactorLeft']}/{park['singleFactorRight']} | "
            f"{classify_park(park)}"
        )

    print()
    print("## Most asymmetric parks")
    asym = sorted(
        parks,
        key=lambda p: (
            abs(p["homeRunFactorLeft"] - p["homeRunFactorRight"])
            + abs(p["singleFactorLeft"] - p["singleFactorRight"]),
            p["ballparkName"],
        ),
        reverse=True,
    )
    for park in asym[:8]:
        print(
            f"- {park['ballparkName']}: "
            f"SI L/R {park['singleFactorLeft']}/{park['singleFactorRight']} | "
            f"HR L/R {park['homeRunFactorLeft']}/{park['homeRunFactorRight']} | "
            f"{classify_park(park)}"
        )


if __name__ == "__main__":
    main()
