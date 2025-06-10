import base64
import json
import requests
import os

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
REPO_OWNER = "saberloty"
REPO_NAME = "bot-data"
FILE_PATH = "users.json"

API_URL = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/{FILE_PATH}"
HEADERS = {"Authorization": f"Bearer {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json"}


def load_users_data():
    response = requests.get(API_URL, headers=HEADERS)
    if response.status_code == 200:
        content = response.json()["content"]
        decoded = base64.b64decode(content).decode("utf-8")
        return json.loads(decoded)
    else:
        print("خطا در بارگذاری اطلاعات از گیت‌هاب:", response.text)
        return {}


def save_users_data(data: dict):
    get_resp = requests.get(API_URL, headers=HEADERS)
    if get_resp.status_code == 200:
        sha = get_resp.json()["sha"]
    else:
        print("خطا در دریافت SHA:", get_resp.text)
        return

    encoded_content = base64.b64encode(json.dumps(data, ensure_ascii=False, indent=2).encode()).decode()
    payload = {
        "message": "update users.json",
        "content": encoded_content,
        "sha": sha,
        "branch": "main"
    }

    put_resp = requests.put(API_URL, headers=HEADERS, json=payload)
    if put_resp.status_code not in [200, 201]:
        print("خطا در ذخیره اطلاعات در گیت‌هاب:", put_resp.text)
