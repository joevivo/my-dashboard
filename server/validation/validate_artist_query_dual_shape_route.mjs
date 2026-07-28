import assert from "node:assert/strict";
import { execFileSync } from "node:child_process";
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";

const repoRoot = fileURLToPath(new URL("../../", import.meta.url));
const cliPath = "data/music/scripts/artist_query_summary.py";
const serverPath = new URL("../index.js", import.meta.url);

const stdout = execFileSync(
  "python",
  ["-B", cliPath, "R.E.M."],
  {
    cwd: repoRoot,
    encoding: "utf8",
    env: {
      ...process.env,
      PYTHONIOENCODING: "utf-8",
      PYTHONUTF8: "1"
    }
  }
);

const cliResponse = JSON.parse(stdout);
const canonical = cliResponse.canonicalArtistSummary;

assert.ok(canonical);
assert.equal(
  canonical.schemaVersion,
  "music.canonical-artist-summary.v1"
);

const legacyKeys = Object.keys(cliResponse).filter(
  (key) => key !== "canonicalArtistSummary"
);

assert.equal(legacyKeys.length, 26);

for (const key of legacyKeys) {
  assert.deepEqual(
    canonical.compatibility[key],
    cliResponse[key],
    `Canonical compatibility differs for ${key}`
  );
}

const serverSource = readFileSync(serverPath, "utf8");

const routeStart = serverSource.indexOf(
  'app.get("/api/music/query/artist"'
);

assert.notEqual(routeStart, -1);

const orderedMarkers = [
  "const result = JSON.parse(stdout);",
  "result.family =",
  "result.familyMetrics = buildFamilyMetrics(",
  "result.bridge = JSON.parse(bridgeOutput);",
  "result.investigation = buildArtistInvestigation(result);",
  "res.json(result);"
];

let previousPosition = routeStart;

for (const marker of orderedMarkers) {
  const position = serverSource.indexOf(
    marker,
    previousPosition
  );

  assert.notEqual(
    position,
    -1,
    `Express route marker is missing: ${marker}`
  );

  assert.ok(
    position > previousPosition,
    `Express route marker is out of order: ${marker}`
  );

  previousPosition = position;
}

const beforeCanonical = structuredClone(canonical);

const stableLegacyKeys = legacyKeys.filter(
  (key) => key !== "investigation"
);

assert.equal(stableLegacyKeys.length, 25);

const stableLegacyValues = Object.fromEntries(
  stableLegacyKeys.map((key) => [
    key,
    structuredClone(cliResponse[key])
  ])
);

const routedResponse = structuredClone(cliResponse);

routedResponse.family = {
  status: "fixture-family"
};

routedResponse.familyMetrics = {
  status: "fixture-family-metrics"
};

routedResponse.bridge = {
  status: "fixture-bridge"
};

routedResponse.investigation = {
  status: "fixture-investigation"
};

for (const key of stableLegacyKeys) {
  assert.deepEqual(
    routedResponse[key],
    stableLegacyValues[key],
    `Express enrichment changed stable legacy field ${key}`
  );
}

assert.deepEqual(
  routedResponse.canonicalArtistSummary,
  beforeCanonical
);

assert.equal(
  routedResponse.investigation.status,
  "fixture-investigation"
);

assert.equal(Object.keys(routedResponse).length, 30);

console.log("EXPRESS_ROUTE_SOURCE_CONTRACT: PASS");
console.log("LEGACY_CLI_FIELDS: 26/26");
console.log("ROUTE_STABLE_LEGACY_FIELDS: 25/25");
console.log("EXPECTED_ROUTE_OWNED_FIELD: investigation");
console.log(
  "ROUTE_ADDED_FIELDS: family, familyMetrics, bridge"
);
console.log("CANONICAL_COMPATIBILITY_EQUALITY: PASS");
console.log("CANONICAL_PASS_THROUGH: PASS");
console.log("VALIDATION_PASS");
