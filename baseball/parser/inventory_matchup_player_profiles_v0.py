from __future__ import annotations

from fractions import Fraction
from pathlib import Path
import json
from typing import Any, Callable


PROFILE_PATH = Path("data/baseball/parsed/strat365/1980/matchup-player-profiles/1980.matchup-player-profiles.json")


def frac(payload: dict[str, Any] | None) -> Fraction:
    if not payload:
        return Fraction(0, 1)
    return Fraction(payload["numerator"], payload["denominator"])


def fmt(value: Fraction) -> str:
    return f"{float(value):.4f}"


def avg(profile: dict[str, Any], key: str) -> Fraction:
    return frac(profile.get("averages", {}).get(key))


def outcome(profile: dict[str, Any], key: str) -> Fraction:
    return frac(profile.get("outcomeAverages", {}).get(key))


def label(profile: dict[str, Any]) -> str:
    player = profile.get("player", {})
    return (
        f'{player.get("playerName")} '
        f'team={player.get("team")} '
        f'exact={profile.get("exactMatchups")} '
        f'partial={profile.get("partialMatchups")}'
    )


def print_top(
    title: str,
    profiles: list[dict[str, Any]],
    get_value: Callable[[dict[str, Any]], Fraction],
    *,
    limit: int = 15,
    reverse: bool = True,
) -> None:
    print()
    print(title)
    print("-" * 72)

    ranked = sorted(profiles, key=lambda profile: (get_value(profile), label(profile)), reverse=reverse)

    for profile in ranked[:limit]:
        print(f"{fmt(get_value(profile))}  {label(profile)}")


def main() -> None:
    data = json.loads(PROFILE_PATH.read_text(encoding="utf-8-sig", errors="replace"))

    hitters = data.get("hitterProfiles", [])
    pitchers = data.get("pitcherProfiles", [])

    exact_hitters = [profile for profile in hitters if profile.get("exactMatchups", 0) > 0]
    exact_pitchers = [profile for profile in pitchers if profile.get("exactMatchups", 0) > 0]
    unresolved_hitters = [profile for profile in hitters if profile.get("exactMatchups", 0) == 0]
    unresolved_pitchers = [profile for profile in pitchers if profile.get("exactMatchups", 0) == 0]

    print("BIE Matchup Player Profile Inventory v0")
    print("=" * 72)
    print(f"Rows: {data.get('rowCount')}")
    print(f"Exact rows: {data.get('exactRows')}")
    print(f"Partial rows: {data.get('partialRows')}")
    print(f"Hitter profiles: {len(hitters)}")
    print(f"Pitcher profiles: {len(pitchers)}")
    print(f"Rankable exact hitter profiles: {len(exact_hitters)}")
    print(f"Rankable exact pitcher profiles: {len(exact_pitchers)}")
    print(f"Unresolved-only hitter profiles: {len(unresolved_hitters)}")
    print(f"Unresolved-only pitcher profiles: {len(unresolved_pitchers)}")

    if unresolved_hitters:
        print()
        print("Unresolved-only hitters excluded from ranked averages")
        print("-" * 72)
        for profile in unresolved_hitters:
            print(label(profile))

    if unresolved_pitchers:
        print()
        print("Unresolved-only pitchers excluded from ranked averages")
        print("-" * 72)
        for profile in unresolved_pitchers:
            print(label(profile))

    print_top(
        "Top hitters by average on-base candidate weight",
        exact_hitters,
        lambda profile: avg(profile, "onBaseCandidateWeight"),
    )

    print_top(
        "Top hitters by average hit candidate weight",
        exact_hitters,
        lambda profile: avg(profile, "hitCandidateWeight"),
    )

    print_top(
        "Top hitters by average home run weight",
        exact_hitters,
        lambda profile: outcome(profile, "HOME_RUN"),
    )

    print_top(
        "Lowest hitters by average strikeout weight",
        exact_hitters,
        lambda profile: outcome(profile, "STRIKEOUT"),
        reverse=False,
    )

    print_top(
        "Best pitchers by lowest average opponent on-base candidate weight",
        exact_pitchers,
        lambda profile: avg(profile, "onBaseCandidateWeight"),
        reverse=False,
    )

    print_top(
        "Best pitchers by lowest average opponent hit candidate weight",
        exact_pitchers,
        lambda profile: avg(profile, "hitCandidateWeight"),
        reverse=False,
    )

    print_top(
        "Best pitchers by lowest average opponent home run weight",
        exact_pitchers,
        lambda profile: outcome(profile, "HOME_RUN"),
        reverse=False,
    )

    print_top(
        "Best pitchers by average strikeout weight",
        exact_pitchers,
        lambda profile: outcome(profile, "STRIKEOUT"),
    )

    print_top(
        "Avoid-list pitchers by highest average opponent on-base candidate weight",
        exact_pitchers,
        lambda profile: avg(profile, "onBaseCandidateWeight"),
    )

    print_top(
        "Avoid-list pitchers by highest average opponent home run weight",
        exact_pitchers,
        lambda profile: outcome(profile, "HOME_RUN"),
    )

    print("=" * 72)


if __name__ == "__main__":
    main()
