from pathlib import Path
import json
import re

ROOT = Path.cwd()
print("BIE Auth Diagnostic 001")
print("=" * 72)
print(f"Repo root: {ROOT}")
print()

TARGET_PLAYER_ID = "35273"
TARGET_SEASON = "1980"

candidate_card = ROOT / "data" / "baseball" / "raw" / "strat365" / TARGET_SEASON / "cards" / f"{TARGET_PLAYER_ID}.html"

print("1) Captured card evidence")
print("-" * 72)

if candidate_card.exists():
    text = candidate_card.read_text(encoding="utf-8", errors="replace")
    print(f"Card file: {candidate_card}")
    print(f"Size bytes: {candidate_card.stat().st_size}")
    print(f"Contains gated-shell message: {'must have purchased and be logged in' in text}")
    print(f"Contains Balance: {'Balance' in text}")
    print(f"Contains Defense: {'Defense' in text}")
    print(f"Contains Running: {'Running' in text}")
    print(f"Contains SINGLE: {'SINGLE' in text}")
    print(f"Contains HOMERUN: {'HOMERUN' in text}")
    print(f"HTML table count: {len(re.findall(r'<table\\b', text, flags=re.I))}")

    title_match = re.search(r"<title[^>]*>(.*?)</title>", text, flags=re.I | re.S)
    if title_match:
        title = re.sub(r"\s+", " ", title_match.group(1)).strip()
        print(f"HTML title: {title}")

    print()
    print("Nearby gated-shell text:")
    marker = "must have purchased"
    idx = text.find(marker)
    if idx >= 0:
        start = max(0, idx - 200)
        end = min(len(text), idx + 400)
        print(re.sub(r"\s+", " ", text[start:end]).strip())
    else:
        print("(marker not found)")
else:
    print(f"Missing expected card file: {candidate_card}")

print()
print("2) Metadata files for target player")
print("-" * 72)

metadata_hits = []
for pattern in [
    f"**/*{TARGET_PLAYER_ID}*.json",
    f"**/*{TARGET_PLAYER_ID}*.metadata",
    f"**/*{TARGET_PLAYER_ID}*.meta",
]:
    metadata_hits.extend(ROOT.glob(pattern))

metadata_hits = sorted(set(metadata_hits))

if not metadata_hits:
    print("No metadata files found for target player.")
else:
    for path in metadata_hits[:20]:
        print(f"\nMetadata candidate: {path}")
        try:
            raw = path.read_text(encoding="utf-8", errors="replace")
            print(raw[:2000])
        except Exception as exc:
            print(f"Could not read: {exc}")

print()
print("3) Capture/session implementation scan")
print("-" * 72)

keywords = [
    "requests.Session",
    "Session(",
    ".get(",
    ".post(",
    "cookies",
    "Cookie",
    "headers",
    "User-Agent",
    "Referer",
    "csrf",
    "auth",
    "login",
    "strat",
    "365.strat-o-matic.com",
]

py_files = sorted((ROOT / "baseball").glob("**/*.py")) if (ROOT / "baseball").exists() else []
if not py_files:
    py_files = sorted(ROOT.glob("**/baseball/**/*.py"))

interesting = []

for path in py_files:
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        continue

    hits = [k for k in keywords if k.lower() in text.lower()]
    if hits:
        interesting.append((path, hits, text))

print(f"Python files scanned: {len(py_files)}")
print(f"Potentially relevant files: {len(interesting)}")

for path, hits, text in interesting[:20]:
    rel = path.relative_to(ROOT) if path.is_relative_to(ROOT) else path
    print()
    print(f"FILE: {rel}")
    print(f"HITS: {', '.join(hits)}")

    lines = text.splitlines()
    for i, line in enumerate(lines, start=1):
        lower = line.lower()
        if any(k.lower() in lower for k in keywords):
            start = max(1, i - 2)
            end = min(len(lines), i + 2)
            print(f"\n  Lines {start}-{end}:")
            for j in range(start, end + 1):
                print(f"  {j:04d}: {lines[j-1]}")

print()
print("4) Existing capture summaries")
print("-" * 72)

summary_candidates = []
for pattern in [
    "data/baseball/raw/strat365/1980/**/*summary*.json",
    "data/baseball/raw/strat365/1980/**/*capture*.json",
    "data/baseball/raw/strat365/1980/**/*manifest*.json",
    "data/baseball/**/*summary*.json",
    "data/baseball/**/*manifest*.json",
]:
    summary_candidates.extend(ROOT.glob(pattern))

summary_candidates = sorted(set(summary_candidates))

if not summary_candidates:
    print("No summary/manifest JSON files found.")
else:
    for path in summary_candidates[:15]:
        print(f"\nSummary candidate: {path}")
        try:
            raw = path.read_text(encoding="utf-8", errors="replace")
            print(raw[:2000])
        except Exception as exc:
            print(f"Could not read: {exc}")

print()
print("DIAGNOSTIC COMPLETE")
print("=" * 72)
