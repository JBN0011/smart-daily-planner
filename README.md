# Smart Daily Planner

Type a messy to-do list and get a time-based schedule for your day.

## How it works
```
Messy text -> ai_planner.py (Gemini, or offline rules) -> clean tasks (JSON)
           -> scheduler.py (pure Python time maths)     -> Streamlit table
```
- **AI** understands language: task names, priority, minutes, fixed clock times.
- **Python** places tasks on the clock, because time maths must be exact.
- If there is no API key, quota runs out, or the AI returns bad JSON, the app
  falls back to a simple rule-based parser instead of crashing.

## Features
- Priority sorting (high, medium, low)
- Fixed-time tasks ("meeting at 2 pm") stay at their time
- Lunch break and breaks between tasks
- "Did not fit" list for tasks that cannot fit today
- CSV download and saved history (history.json)

## Setup (Windows PowerShell)
```powershell
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env      # then paste your GEMINI_API_KEY (optional)
streamlit run app.py
```
Run tests: `python tests/test_planner.py`

## Files
| File | Job |
|---|---|
| app.py | Streamlit screen |
| ai_planner.py | Messy text to clean tasks (Gemini + offline fallback) |
| scheduler.py | Builds the timetable |
| storage.py | Saves plans to history.json |
| tests/test_planner.py | 5 automated checks |

## Limits and future ideas
- One day only; no calendar sync yet
- Offline parser is simple (English keywords only)
- Ideas: Google Calendar export, recurring tasks, task categories
