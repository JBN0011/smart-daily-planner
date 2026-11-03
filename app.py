import pandas as pd
import streamlit as st

from ai_planner import analyze_tasks
from scheduler import build_schedule
from storage import load_history, save_plan

st.set_page_config(page_title="Smart Daily Planner", page_icon="🗓️", layout="centered")
st.title("🗓️ Smart Daily Planner")
st.caption("Type your messy to-do list. Get a time-based plan for the day.")

with st.sidebar:
    st.header("Your day")
    start = st.time_input("Day starts", value=pd.Timestamp("09:00").time()).strftime("%H:%M")
    end = st.time_input("Day ends", value=pd.Timestamp("18:00").time()).strftime("%H:%M")
    break_min = st.slider("Break between tasks (min)", 0, 30, 10, step=5)
    lunch_start = st.time_input("Lunch at", value=pd.Timestamp("13:00").time()).strftime("%H:%M")
    lunch_min = st.slider("Lunch length (min)", 0, 90, 45, step=15)

tab_plan, tab_hist = st.tabs(["Plan my day", "History"])

with tab_plan:
    raw = st.text_area(
        "Your tasks",
        height=160,
        placeholder="gym, assignment due tonight, call bank, meeting at 2 pm, buy vegetables",
    )
    if st.button("Plan my day", type="primary"):
        if not raw.strip():
            st.warning("Please type some tasks first.")
        elif end <= start:
            st.warning("Day end time must be after the start time.")
        else:
            with st.spinner("Planning..."):
                tasks, source = analyze_tasks(raw)
                if not tasks:
                    st.error("I could not find any tasks. Try separating them with commas.")
                else:
                    sched, not_fit = build_schedule(tasks, start, end, break_min,
                                                    lunch_start, lunch_min)
                    st.session_state["result"] = (sched, not_fit, source)

    if "result" in st.session_state:
        sched, not_fit, source = st.session_state["result"]
                label = "Gemini AI" if source == "gemini" else source
        st.info("Understood with: " + label)
        c1, c2 = st.columns(2)
        c1.metric("Scheduled", sum(r["Type"] != "Break" for r in sched))
        c2.metric("Did not fit", len(not_fit))

        st.subheader("Today's schedule")
        st.dataframe(pd.DataFrame(sched), use_container_width=True, hide_index=True)
        if not_fit:
            st.warning("These tasks did not fit today. Move them to tomorrow:")
            st.dataframe(pd.DataFrame(not_fit)[["task", "priority", "minutes"]],
                         use_container_width=True, hide_index=True)

        d1, d2 = st.columns(2)
        d1.download_button("⬇️ Download CSV", pd.DataFrame(sched).to_csv(index=False),
                           file_name="my_plan.csv", mime="text/csv")
        if d2.button("💾 Save to history"):
            save_plan(sched, not_fit)
            st.success("Saved.")

with tab_hist:
    history = load_history()
    if not history:
        st.write("No saved plans yet.")
    for item in reversed(history):
        with st.expander(f"Plan saved on {item['saved_at']}"):
            st.dataframe(pd.DataFrame(item["schedule"]), use_container_width=True,
                         hide_index=True)
