from pathlib import Path
import subprocess
import sys

ROOT = Path.cwd()

print("BIE Auth Setup Check 001")
print("=" * 72)
print(f"Repo root: {ROOT}")
print()

# Ensure local auth storage directory exists.
auth_dir = ROOT / ".bie-auth"
auth_dir.mkdir(exist_ok=True)

print("1) Auth storage")
print("-" * 72)
print(f"Auth dir: {auth_dir}")
print(f"Exists: {auth_dir.exists()}")

# Ensure auth artifacts are ignored by git.
gitignore = ROOT / ".gitignore"
ignore_lines = [
    ".bie-auth/",
    "data/baseball/raw/strat365/authenticated/",
]

existing = gitignore.read_text(encoding="utf-8", errors="replace") if gitignore.exists() else ""
changed = False

for line in ignore_lines:
    if line not in existing:
        existing = existing.rstrip() + "\n" + line + "\n"
        changed = True

if changed:
    gitignore.write_text(existing, encoding="utf-8")
    print("Updated .gitignore with local auth/capture protections.")
else:
    print(".gitignore already protects local auth/capture artifacts.")

print()
print("2) Playwright package")
print("-" * 72)

try:
    import playwright  # noqa: F401
    print("Python package: playwright is installed")
    package_ok = True
except Exception as exc:
    print(f"Python package: playwright is NOT installed ({exc})")
    package_ok = False

if not package_ok:
    print()
    print("Installing playwright Python package...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "playwright"])

print()
print("3) Browser runtime")
print("-" * 72)
print("Installing Chromium runtime for Playwright if needed...")
subprocess.check_call([sys.executable, "-m", "playwright", "install", "chromium"])

print()
print("SETUP CHECK COMPLETE")
print("=" * 72)
