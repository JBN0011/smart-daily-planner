"""Pure-Python scheduler. No AI here: time maths must be exact."""
from datetime import datetime, timedelta

ORDER = {"high": 0, "medium": 1, "low": 2}
FMT = "%H:%M"


def _t(text):
    return datetime.strptime(text, FMT)


def _find_slot(blocks, dur, day_start, day_end, brk):
    """Earliest time where a task of length `dur` fits between existing blocks."""
    cand = day_start
    for s, e in sorted(blocks):
        if cand + dur + brk <= s:          # fits before this block (with a break)
            break
        cand = max(cand, e + brk)
    if cand + dur <= day_end:
        return cand
    return None


def build_schedule(tasks, start="09:00", end="18:00", break_min=10,
                   lunch_start="13:00", lunch_min=45):
    """Return (schedule_rows, not_fit_tasks)."""
    day_start, day_end = _t(start), _t(end)
    brk = timedelta(minutes=break_min)
    blocks, rows, not_fit, flexible = [], [], [], []

    # 1. Fixed-time tasks go on the clock first
    for t in tasks:
        if t.get("fixed_time"):
            s = _t(t["fixed_time"])
            e = s + timedelta(minutes=t["minutes"])
            if s < day_start or e > day_end:
                not_fit.append(t)
                continue
            blocks.append((s, e))
            rows.append((s, e, t["task"], t["priority"], "Fixed time"))
        else:
            flexible.append(t)

    # 2. Lunch
    if lunch_min > 0:
        ls = _t(lunch_start)
        le = ls + timedelta(minutes=lunch_min)
        if day_start <= ls and le <= day_end:
            blocks.append((ls, le))
            rows.append((ls, le, "Lunch break", "-", "Break"))

    # 3. Flexible tasks: high priority first, into the earliest free gap
    flexible.sort(key=lambda t: ORDER.get(t["priority"], 1))
    for t in flexible:
        dur = timedelta(minutes=t["minutes"])
        slot = _find_slot(blocks, dur, day_start, day_end, brk)
        if slot is None:
            not_fit.append(t)
            continue
        blocks.append((slot, slot + dur))
        rows.append((slot, slot + dur, t["task"], t["priority"], "Flexible"))

    rows.sort(key=lambda r: r[0])
    schedule = [{"Time": f"{s:%H:%M} - {e:%H:%M}", "Task": name,
                 "Priority": pr, "Type": kind} for s, e, name, pr, kind in rows]
    return schedule, not_fit
