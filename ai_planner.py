"""Turns messy text into clean tasks. Uses Gemini if a key exists,
otherwise a simple rule-based parser (offline fallback)."""
import json
import os
import re

from dotenv import load_dotenv

load_dotenv()

PROMPT = """You are a daily planning assistant.
Read the messy to-do list and return ONLY a JSON list.
Each item must have exactly these keys:
- "task": short clear name
- "priority": "high", "medium" or "low"
- "minutes": estimated time, whole number
- "fixed_time": "HH:MM" (24-hour) if the user gave a clock time, otherwise null
Rules:
- Deadlines, "urgent", "due today/tonight" are "high".
- Do not add tasks the user did not write.
- Split one sentence into separate tasks if it has more than one.
To-do list:
"""

HIGH_WORDS = ("urgent", "asap", "due", "deadline", "tonight", "important", "interview")
LOW_WORDS = ("maybe", "someday", "if time", "optional", "later")
DEFAULT_MIN = {"gym": 60, "call": 15, "email": 15, "reply": 15, "assignment": 90,
               "study": 90, "buy": 30, "shop": 45, "cook": 45, "clean": 30}


def _clean(items):
    """Validate whatever came back so the scheduler never crashes."""
    out = []
    for it in items:
        if not isinstance(it, dict) or not str(it.get("task", "")).strip():
            continue
        pr = str(it.get("priority", "medium")).lower()
        pr = pr if pr in ("high", "medium", "low") else "medium"
        try:
            mins = max(5, min(240, int(it.get("minutes", 30))))
        except (TypeError, ValueError):
            mins = 30
        ft = it.get("fixed_time")
        if not (isinstance(ft, str) and re.fullmatch(r"([01]\d|2[0-3]):[0-5]\d", ft)):
            ft = None
        out.append({"task": str(it["task"]).strip(), "priority": pr,
                    "minutes": mins, "fixed_time": ft})
    return out


def _fallback(raw):
    """Offline parser: splits text and guesses with simple rules."""
    parts = [p.strip() for p in re.split(r"[,\n;]|\band\b", raw) if p.strip()]
    items = []
    for p in parts:
        low = p.lower()
        pr = "high" if any(w in low for w in HIGH_WORDS) else \
             "low" if any(w in low for w in LOW_WORDS) else "medium"
        mins = next((v for k, v in DEFAULT_MIN.items() if k in low), 30)
        m = re.search(r"(\d+)\s*(hours?|hrs?|h|minutes?|mins?|m)\b", low)
        if m:
            mins = int(m.group(1)) * (60 if m.group(2).startswith("h") else 1)
        ft = None
        m = re.search(r"\bat\s+(\d{1,2})(?::(\d{2}))?\s*(am|pm)?", low)
        if m:
            h, mi, ap = int(m.group(1)), int(m.group(2) or 0), m.group(3)
            if ap == "pm" and h < 12:
                h += 12
            if ap == "am" and h == 12:
                h = 0
            if h < 24:
                ft = f"{h:02d}:{mi:02d}"
        items.append({"task": p, "priority": pr, "minutes": mins, "fixed_time": ft})
    return _clean(items)


def analyze_tasks(raw_text):
    """Return (tasks, source) where source is 'gemini' or 'offline'."""
    try:
    import streamlit as st
    key = os.getenv("GEMINI_API_KEY") or st.secrets.get("GEMINI_API_KEY")
except Exception:
    key = os.getenv("GEMINI_API_KEY")
    if not key or key == "your_key_here":
        return _fallback(raw_text), "offline"
    try:
        from google import genai
        client = genai.Client(api_key=key)
        resp = client.models.generate_content(
            model=os.getenv("GEMINI_MODEL", "gemini-2.5-flash"),
            contents=PROMPT + raw_text,
            config={"response_mime_type": "application/json"},
        )
        tasks = _clean(json.loads(resp.text))
        if tasks:
            return tasks, "gemini"
    except Exception:
        pass  # network, quota or bad JSON: fall back instead of crashing
    return _fallback(raw_text), "offline"
