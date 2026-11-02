import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))
import os
os.environ["GEMINI_API_KEY"] = ""          # force offline mode in tests

from ai_planner import analyze_tasks
from scheduler import build_schedule


def test_priority_order():
    tasks = [{"task": "low", "priority": "low", "minutes": 30, "fixed_time": None},
             {"task": "high", "priority": "high", "minutes": 30, "fixed_time": None}]
    s, _ = build_schedule(tasks, lunch_min=0)
    assert s[0]["Task"] == "high" and s[0]["Time"].startswith("09:00")


def test_fixed_time_respected():
    tasks = [{"task": "meeting", "priority": "high", "minutes": 60, "fixed_time": "14:00"}]
    s, _ = build_schedule(tasks)
    assert any(r["Task"] == "meeting" and r["Time"] == "14:00 - 15:00" for r in s)


def test_no_overlap_with_lunch():
    tasks = [{"task": "long", "priority": "high", "minutes": 240, "fixed_time": None}]
    s, nf = build_schedule(tasks, start="09:00", end="18:00")
    lunch = next(r for r in s if r["Task"] == "Lunch break")
    assert lunch["Time"] == "13:00 - 13:45"


def test_too_many_tasks_go_to_not_fit():
    tasks = [{"task": f"t{i}", "priority": "medium", "minutes": 120, "fixed_time": None}
             for i in range(10)]
    _, nf = build_schedule(tasks)
    assert len(nf) > 0


def test_offline_parser():
    tasks, src = analyze_tasks("gym, assignment due tonight, meeting at 2 pm for 1 hour")
    assert src == "offline" and len(tasks) == 3
    assert tasks[1]["priority"] == "high"
    assert tasks[2]["fixed_time"] == "14:00" and tasks[2]["minutes"] == 60


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn(); print("PASS", name)
