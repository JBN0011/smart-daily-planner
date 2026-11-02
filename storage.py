"""Saves planned days to a small JSON file."""
import json
from datetime import datetime
from pathlib import Path

FILE = Path(__file__).parent / "history.json"


def load_history():
    try:
        return json.loads(FILE.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def save_plan(schedule, not_fit):
    data = load_history()
    data.append({"saved_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
                 "schedule": schedule, "not_fit": not_fit})
    FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")
