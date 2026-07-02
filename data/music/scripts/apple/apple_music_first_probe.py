import os
import time
import jwt
import requests

TEAM_ID = os.environ["APPLE_TEAM_ID"]
KEY_ID = os.environ["APPLE_KEY_ID"]
KEY_PATH = os.environ["APPLE_PRIVATE_KEY_PATH"]

with open(KEY_PATH, "r", encoding="utf-8") as f:
    private_key = f.read()

now = int(time.time())

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
print("DEVELOPER_TOKEN_START:", developer_token[:40])
print("DEVELOPER_TOKEN_END:", developer_token[-40:])

url = "https://api.music.apple.com/v1/catalog/us/search"
params = {
    "term": "R.E.M. Green",
    "types": "albums",
    "limit": 3,
}
headers = {
    "Authorization": f"Bearer {developer_token}",
}

response = requests.get(url, headers=headers, params=params, timeout=30)
print("Status:", response.status_code)
with open("data/music/apple_green_catalog_probe.json", "w", encoding="utf-8") as f:
    f.write(response.text)
print("Saved: data/music/apple_green_catalog_probe.json")
