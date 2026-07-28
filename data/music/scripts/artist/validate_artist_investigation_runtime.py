from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile


ARTIST_DIR = Path(__file__).resolve().parent
SCRIPTS_DIR = ARTIST_DIR.parent
REPO_ROOT = Path(__file__).resolve().parents[4]
JS_BUILDER = (
    REPO_ROOT
    / "server"
    / "lib"
    / "investigationBuilder.js"
)

sys.path.insert(0, str(ARTIST_DIR))
sys.path.insert(0, str(SCRIPTS_DIR))

from artist_investigation_runtime import (  # noqa: E402
    apply_investigation_projection,
    build_artist_investigation,
)
from artist_query_core import ArtistQueryEngine  # noqa: E402


def run_javascript_builder(
    payload: dict,
) -> dict:
    node_source = """
import fs from "fs";
import { pathToFileURL } from "url";

const inputPath = process.argv[2];
const builderPath = process.argv[3];

const { buildArtistInvestigation } = await import(
  pathToFileURL(builderPath).href
);

const payload = JSON.parse(
  fs.readFileSync(inputPath, "utf8")
);

console.log(JSON.stringify(
  buildArtistInvestigation(payload)
));
""".strip()

    environment = os.environ.copy()

    with tempfile.TemporaryDirectory() as directory:
        temporary = Path(directory)
        input_path = temporary / "input.json"
        script_path = temporary / "probe.mjs"

        input_path.write_text(
            json.dumps(
                payload,
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )

        script_path.write_text(
            node_source + "\n",
            encoding="utf-8",
        )

        output = subprocess.check_output(
            [
                "node",
                str(script_path),
                str(input_path),
                str(JS_BUILDER),
            ],
            cwd=REPO_ROOT,
            env=environment,
        )

    return json.loads(output.decode("utf-8"))


synthetic = {
    "query": "Sugar",
    "artist": "Sugar",
    "actualPlays": 10,
    "actualSkips": 2,
    "hoursListened": 1.5,
    "libraryEvidenceRecords": 3,
    "yearsActive": 2,
    "playActivitySource": (
        "apple_music_daily_track_summary"
    ),
    "source": "apple_music_library_tracks",
    "family": {
        "familyName": "Bob Mould Family",
        "members": ["Bob Mould", "Sugar"],
        "relationshipType": "curated",
    },
    "familyMetrics": {
        "actualPlays": 25,
    },
    "bridge": {
        "live": {
            "recentObjectCount": 2,
        },
        "facts": [
            {
                "type": "continuity",
                "statement": "Continuity evidence exists.",
                "value": 4,
                "evidence": ["historical", "live"],
            },
            {
                "type": (
                    "recent_apple_snapshot_history"
                ),
                "statement": (
                    "Snapshot evidence exists."
                ),
                "value": None,
                "evidence": [
                    "apple_snapshot_warehouse"
                ],
            },
        ],
    },
}

python_synthetic = build_artist_investigation(
    synthetic
)

javascript_synthetic = run_javascript_builder(
    synthetic
)

assert python_synthetic == javascript_synthetic

assert set(python_synthetic) == {
    "confidence",
    "entity",
    "evidence",
    "facts",
    "hypotheses",
    "identity",
    "insights",
    "openQuestions",
    "question",
    "reasoningTrace",
    "suggestedInvestigations",
}

assert len(python_synthetic["facts"]) == 6
assert len(python_synthetic["evidence"]) == 4
assert len(python_synthetic["reasoningTrace"]) == 5

engine = ArtistQueryEngine()
legacy = engine.query_artist("Sugar")

environment = os.environ.copy()
environment["PYTHONIOENCODING"] = "utf-8"
environment["PYTHONUTF8"] = "1"

output = subprocess.check_output(
    [
        sys.executable,
        "-B",
        "data/music/scripts/artist_query_summary.py",
        "Sugar",
    ],
    cwd=REPO_ROOT,
    env=environment,
)

integrated = json.loads(output.decode("utf-8"))
canonical = integrated["canonicalArtistSummary"]

route_style_result = {
    **{
        key: integrated[key]
        for key in legacy
    },
    "family": canonical["compatibility"][
        "family"
    ],
    "familyMetrics": canonical["compatibility"][
        "familyMetrics"
    ],
    "bridge": canonical["compatibility"]["bridge"],
}

javascript_actual = run_javascript_builder(
    route_style_result
)

assert canonical["investigation"] == javascript_actual

assert (
    canonical["suggestedInvestigations"]
    == javascript_actual[
        "suggestedInvestigations"
    ]
)

assert len(legacy) == 26
assert len(integrated) == 27

for key, value in legacy.items():
    assert integrated[key] == value
    assert canonical["compatibility"][key] == value

projected = apply_investigation_projection(
    {"investigation": {}, "suggestedInvestigations": []},
    python_synthetic,
)

assert projected["investigation"] == python_synthetic
assert projected["suggestedInvestigations"] == []

print("ARTIST_INVESTIGATION_FIXTURES: 7/7")
print("EXPRESS_INVESTIGATION_KEY_PARITY: PASS")
print("EXPRESS_INVESTIGATION_VALUE_PARITY: PASS")
print("INVESTIGATION_FACT_PARITY: PASS")
print("INVESTIGATION_EVIDENCE_PARITY: PASS")
print("INVESTIGATION_REASONING_TRACE_PARITY: PASS")
print("CLI_LEGACY_FIELD_EQUALITY: 26/26")
print("CLI_CANONICAL_INVESTIGATION_INTEGRATION: PASS")
print("VALIDATION_PASS")
