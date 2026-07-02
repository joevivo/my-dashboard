import os, time, json
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
OUT_DIR.mkdir(parents=True, exist_ok=True)

endpoints = {
    "library_albums": "/v1/me/library/albums",
    "library_playlists": "/v1/me/library/playlists",
    "library_songs": "/v1/me/library/songs",
    "recent_played": "/v1/me/recent/played",
    "heavy_rotation": "/v1/me/history/heavy-rotation",
}

private_key = KEY_PATH.read_text(encoding="utf-8")
music_user_token = USER_TOKEN_PATH.read_text(encoding="utf-8").strip()

now = int(time.time())
developer_token = jwt.encode(
    {"iss": TEAM_ID, "iat": now, "exp": now + 3600},
    private_key,
    algorithm="ES256",
    headers={"alg": "ES256", "kid": KEY_ID},
)

headers = {
    "Authorization": f"Bearer {developer_token}",
    "Music-User-Token": music_user_token,
}

captured_at = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

def fetch_all(path, limit=100, max_pages=50):
    url = BASE_URL + path
    params = {"limit": limit}
    items = []
    pages = 0
    status = None

    while url and pages < max_pages:
        pages += 1
        response = requests.get(url, headers=headers, params=params, timeout=30)
        status = response.status_code
        payload = response.json() if response.text else {}

        if status != 200:
            return status, pages, items, payload

        items.extend(payload.get("data") or [])
        next_path = payload.get("next")
        url = urljoin(BASE_URL, next_path) if next_path else None
        params = None

    return status or 0, pages, items, {"data": items}

manifest = {
    "capturedAt": captured_at,
    "runId": RUN_ID,
    "endpoints": {},
}

for name, path in endpoints.items():
    max_pages = 5 if name == "library_songs" else 50
    limit = 100 if name in {"library_albums", "library_playlists", "library_songs"} else None
    status, pages, items, error_payload = fetch_all(path, limit=limit, max_pages=max_pages)

    out_file = OUT_DIR / f"apple_{name}.json"
    payload = {
        "status": status,
        "url": path,
        "capturedAt": captured_at,
        "pageCount": pages,
        "itemCount": len(items),
        "response": {"data": items},
    }

    if status != 200:
        payload["error"] = error_payload

    out_file.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    manifest["endpoints"][name] = {
        "status": status,
        "pages": pages,
        "items": len(items),
        "file": str(out_file).replace("\\", "/"),
    }

    print(f"{name}: {status} | pages: {pages} | items: {len(items)}")

manifest_file = OUT_DIR / "apple_snapshot_manifest.json"
manifest_file.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

print(f"Saved snapshot: {OUT_DIR}")
