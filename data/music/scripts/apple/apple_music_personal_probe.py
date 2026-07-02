import os, time, jwt, requests

TEAM_ID = "5VDR2C375R"
KEY_ID = "UQ32JKQ8DL"
KEY_PATH = os.path.join(os.environ["USERPROFILE"], "apple-dev-keys", "AuthKey_UQ32JKQ8DL.p8")
USER_TOKEN_PATH = os.path.join(os.environ["USERPROFILE"], "apple-dev-keys", "music_user_token.txt")

with open(KEY_PATH, "r", encoding="utf-8") as f:
    private_key = f.read()

with open(USER_TOKEN_PATH, "r", encoding="utf-8") as f:
    music_user_token = f.read().strip()

now = int(time.time())
developer_token = jwt.encode(
    {"iss": TEAM_ID, "iat": now, "exp": now + 3600},
    private_key,
    algorithm="ES256",
    headers={"alg": "ES256", "kid": KEY_ID},
)

url = "https://api.music.apple.com/v1/me/library/songs"
headers = {
    "Authorization": f"Bearer {developer_token}",
    "Music-User-Token": music_user_token,
}
params = {"limit": 5}

response = requests.get(url, headers=headers, params=params, timeout=30)
print("Status:", response.status_code)
print(response.text[:2000])
