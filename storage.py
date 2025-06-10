import os
import json
from github import Github

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
REPO_NAME = "saberloty/bot-data"
FILE_PATH = "users.json"
COMMIT_MESSAGE = "update users.json"

def upload_to_github(content: str):
    g = Github(GITHUB_TOKEN)
    repo = g.get_repo(REPO_NAME)
    try:
        contents = repo.get_contents(FILE_PATH)
        repo.update_file(contents.path, COMMIT_MESSAGE, content, contents.sha)
    except:
        repo.create_file(FILE_PATH, COMMIT_MESSAGE, content)

def download_from_github() -> str:
    g = Github(GITHUB_TOKEN)
    repo = g.get_repo(REPO_NAME)
    try:
        contents = repo.get_contents(FILE_PATH)
        return contents.decoded_content.decode()
    except:
        return json.dumps({})
