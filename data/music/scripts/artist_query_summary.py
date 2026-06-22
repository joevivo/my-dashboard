from __future__ import annotations

import json
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
ARTIST_MODULE_DIR = SCRIPT_DIR / "artist"

if str(ARTIST_MODULE_DIR) not in sys.path:
    sys.path.insert(0, str(ARTIST_MODULE_DIR))

from artist_query_core import ArtistQueryEngine


def main() -> int:
    if len(sys.argv) < 2:
        print(json.dumps({"error": "Artist name required"}))
        return 1

    query = sys.argv[1].strip()

    try:
        engine = ArtistQueryEngine()
        result = engine.query_artist(query)
    except Exception as error:
        print(json.dumps({"error": str(error), "query": query}, ensure_ascii=False))
        return 1

    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
