from __future__ import annotations

import json
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
ARTIST_MODULE_DIR = SCRIPT_DIR / "artist"

if str(ARTIST_MODULE_DIR) not in sys.path:
    sys.path.insert(0, str(ARTIST_MODULE_DIR))

from artist_query_core import ArtistQueryEngine
from canonical_artist_summary import (
    assemble_canonical_artist_summary,
    validate_canonical_artist_summary,
)
from artist_family_runtime import (
    build_family_metrics,
    resolve_artist_family,
)
from artist_bridge_runtime import (
    build_artist_bridge,
    comparative_standing_from_bridge,
)
from artist_investigation_runtime import (
    apply_investigation_projection,
    build_artist_investigation,
)


def main() -> int:
    if len(sys.argv) < 2:
        print(json.dumps({"error": "Artist name required"}))
        return 1

    query = sys.argv[1].strip()

    try:
        engine = ArtistQueryEngine()
        legacy_result = engine.query_artist(query)

        family = resolve_artist_family(
            legacy_result.get("artist") or query
        )

        family_metrics = build_family_metrics(
            family,
            engine.query_artist,
        )

        bridge = build_artist_bridge(
            legacy_result.get("artist") or query
        )

        comparative_standing = (
            comparative_standing_from_bridge(bridge)
        )

        canonical_result = assemble_canonical_artist_summary(
            legacy_result,
            query=query,
            bridge=bridge,
            comparative_standing=comparative_standing,
            family=family,
            family_metrics=family_metrics,
        )

        route_style_result = {
            **legacy_result,
            "family": family,
            "familyMetrics": family_metrics,
            "bridge": bridge,
        }

        investigation = build_artist_investigation(
            route_style_result
        )

        canonical_result = apply_investigation_projection(
            canonical_result,
            investigation,
        )

        validate_canonical_artist_summary(
            canonical_result
        )

        result = {
            **legacy_result,
            "canonicalArtistSummary": canonical_result,
        }
    except Exception as error:
        print(json.dumps({"error": str(error), "query": query}, ensure_ascii=False))
        return 1

    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
