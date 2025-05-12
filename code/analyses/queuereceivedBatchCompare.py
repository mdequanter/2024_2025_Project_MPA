import plotly.graph_objects as go
import pandas as pd
import re
from collections import defaultdict

# === Input files ===
logfiles = [
    f"code/analyses/logfiles/TSCH_50_{i}.testlog" for i in range(1, 5)
]

# === Helper function ===
def parse_log(logfile):
    queue1_per_minute = defaultdict(list)
    queue2_per_minute = defaultdict(list)
    recv_per_minute = defaultdict(int)

    try:
        with open(logfile, 'r') as file:
            for line in file:
                # Queue fill parsing
                match_queue = re.search(r'queue\s+(\d+)/64\s+(\d+)/64', line)
                if match_queue:
                    tick_match = re.match(r'^(\d+)', line)
                    if tick_match:
                        tick = int(tick_match.group(1))
                        minute = tick // 1_000_000 // 60
                        q1 = int(match_queue.group(1))
                        q2 = int(match_queue.group(2))
                        queue1_per_minute[minute].append(q1)
                        queue2_per_minute[minute].append(q2)

                # Message received by Node 16
                match_recv = re.match(r'^(\d+)\s+16\s+Data received from .*?: \'Msg ', line)
                if match_recv:
                    tick = int(match_recv.group(1))
                    minute = tick // 1_000_000 // 60
                    recv_per_minute[minute] += 1
    except FileNotFoundError:
        print(f"⚠️ File not found: {logfile}")
        return pd.DataFrame()

    # Create DataFrame
    all_minutes = sorted(set(queue1_per_minute.keys()) | set(queue2_per_minute.keys()) | set(recv_per_minute.keys()))
    records = []
    for minute in all_minutes:
        avg_q1 = sum(queue1_per_minute[minute]) / len(queue1_per_minute[minute]) if queue1_per_minute[minute] else 0
        avg_q2 = sum(queue2_per_minute[minute]) / len(queue2_per_minute[minute]) if queue2_per_minute[minute] else 0
        received = recv_per_minute.get(minute, 0)
        records.append({
            "Minute": minute,
            "Avg Queue 1": avg_q1,
            "Avg Queue 2": avg_q2,
            "Messages Received (Node 16)": received
        })

    df = pd.DataFrame(records)
    return df

# === Plotting ===
fig = go.Figure()

for i, path in enumerate(logfiles, start=1):
    df = parse_log(path)
    if df.empty:
        continue

    fig.add_trace(go.Scatter(
        x=df["Minute"], y=df["Avg Queue 1"],
        mode="lines+markers", name=f"Batch {i} - Q1",
        line=dict(dash="dot"), yaxis="y1"
    ))
    fig.add_trace(go.Scatter(
        x=df["Minute"], y=df["Avg Queue 2"],
        mode="lines+markers", name=f"Batch {i} - Q2",
        line=dict(dash="dash"), yaxis="y1"
    ))
    fig.add_trace(go.Scatter(
        x=df["Minute"], y=df["Messages Received (Node 16)"],
        mode="lines+markers", name=f"Batch {i} - Received",
        line=dict(width=2), yaxis="y2"
    ))

# === Layout ===
fig.update_layout(
    title="Queue Usage and Messages Received per Batch",
    xaxis=dict(title="Time (minutes)"),
    yaxis=dict(title="Avg Queue Fill (0–64)", side="left"),
    yaxis2=dict(title="Messages Received", overlaying="y", side="right"),
    legend_title_text="Legend",
    template="plotly_white",
    height=700
)

fig.show()
