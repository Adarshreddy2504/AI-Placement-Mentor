import json
import os

CHATS_FILE = "chats.json"


def load_chats():
    if os.path.exists(CHATS_FILE):
        try:
            with open(CHATS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, dict):
                    return data
        except (json.JSONDecodeError, IOError):
            pass
    return {}


def save_chats(chats):
    try:
        with open(CHATS_FILE, "w", encoding="utf-8") as f:
            json.dump(chats, f, indent=2, ensure_ascii=False)
    except IOError:
        pass
