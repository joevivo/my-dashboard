import json
import os
import time
from pathlib import Path
from urllib.parse import urljoin

import jwt
import requests


TEAM_ID = "5VDR2C375R"
KEY_ID = "UQ32JKQ8DL"
KEY_PATH = Path(os.environ["USERPROFILE"]) / "apple-dev-keys" / "AuthKey_UQ32JKQ8DL.p8"
USER_TOKEN_PATH = Path(os.environ["USERPROFILE"]) / "apple-dev-keys" / "music_user_token.txt"

BASE_URL = "https://api.music.apple.com"
LIVE_ROOT = Path("data/music/live")
RUN_ID = time.strftime("%Y-%m-%d_%H%M%SZ", time.gmtime())
OUT_DIR = LIVE_ROOT / "history" / RUN_ID

ENDPOINTS = {
    "recent_played": "/v1/me/recent/played",
    "heavy_rotation": "/v1/me/history/heavy-rotation",
}


def build_headers():
    now = int(time.time())

    private_key = KEY_PATH.read_text(encoding="utf-8")
    music_user_token = USER_TOKEN_PATH.read_text(encoding="utf-8").strip()

    developer_token = jwt.encode(
        {
            "iss": TEAM_ID,
            "iat": now,
            "exp": now + 3600,
        },
        private_key,
        algorithm="ES256",
        headers={
            "alg": "ES256",
            "kid": KEY_ID,
        },
    )

    return {
        "Authorization": f"Bearer {developer_token}",
        "Music-User-Token": music_user_token,
    }


def fetch_all(path, *, headers, max_pages=50):
    items = []
    pages = 0
    next_path = path
    status = None
    error_payload = None

    while next_path and pages < max_pages:
        url = next_path if next_path.startswith("http") else urljoin(BASE_URL, next_path)
        response = requests.get(url, headers=headers, timeout=30)
        status = response.status_code

        try:
            payload = response.json()
        except ValueError:
            payload = {
                "raw": response.text,
            }

        if response.status_code >= 400:
            error_payload = payload
            break

        items.extend(payload.get("data") or [])
        next_path = payload.get("next")
        pages += 1

    return status, pages, items, error_payload


def write_endpoint(name, path, *, headers, captured_at):
    status, pages, items, error_payload = fetch_all(path, headers=headers)

    payload = {
        "capturedAt": captured_at,
        "endpoint": path,
        "status": status,
        "pages": pages,
        "itemCount": len(items),
        "response": {
            "data": items,
        },
    }

    if error_payload is not None:
        payload["error"] = error_payload

    out_file = OUT_DIR / f"apple_{name}.json"
    out_file.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print(f"{name}: status={status} pages={pages} items={len(items)} file={out_file}")

    if status is None or status >= 400:
        raise RuntimeError(f"Apple dashboard snapshot failed for {name}: status={status}")

    return {
        "name": name,
        "endpoint": path,
        "status": status,
        "pages": pages,
        "itemCount": len(items),
        "file": str(out_file),
    }


def main():
    captured_at = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    headers = build_headers()
    results = []

    for name, path in ENDPOINTS.items():
        results.append(write_endpoint(name, path, headers=headers, captured_at=captured_at))

    manifest = {
        "snapshotId": RUN_ID,
        "capturedAt": captured_at,
        "source": "apple_music_dashboard_live_snapshot",
        "endpoints": results,
    }

    manifest_file = OUT_DIR / "apple_snapshot_manifest.json"
    manifest_file.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print(f"Saved dashboard snapshot: {OUT_DIR}")


if __name__ == "__main__":
    main()
