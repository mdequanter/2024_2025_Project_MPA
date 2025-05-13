import re
from collections import defaultdict
import pandas as pd
import plotly.graph_objects as go
import argparse


# === Configuration ===
parser = argparse.ArgumentParser(description="Parse COOJA test log.")
parser.add_argument("input_path", help="Path to the COOJA log file")
args = parser.parse_args()

logfile = args.input_path

# === CONFIG ===
queue_size = 64
included_nodes = {'3', '6', '16', '25', '26'}
fixed_colors = {
    '3': 'blue',
    '6': 'red',
    '16': 'black',
    '25': 'orange',
    '26': 'brown',
    'received': 'green'
}

# === DATA STRUCTURES ===
queue_q1 = defaultdict(lambda: defaultdict(list))
queue_q2 = defaultdict(lambda: defaultdict(list))
recv_per_minute = defaultdict(int)
total_sent = 0
total_received = 0

# === PARSE LOG ===
with open(logfile, 'r') as f:
    lines = f.readlines()

for line in lines:
    tick_match = re.match(r'^(\d+)', line)
    if not tick_match:
        continue
    tick = int(tick_match.group(1))
    minute = tick // 1_000_000 // 60

    # Queue match
    match = re.match(r'^\d+\s+(\d+)\s+.*?queue\s+(\d+)/\d+\s+(\d+)/\d+', line)
    if match:
        node, q1, q2 = match.group(1), int(match.group(2)), int(match.group(3))
        if node in included_nodes:
            queue_q1[node][minute].append(q1)
            queue_q2[node][minute].append(q2)

    # Received messages by node 16
    if re.match(r'^\d+\s+16\s+Data received from .*?\'Msg ', line):
        recv_per_minute[minute] += 1
        total_received += 1

    # Sent messages
    if "Sending message: 'Msg " in line:
        total_sent += 1

# === PLOT ===
fig = go.Figure()

# Queue traces
for node in sorted(included_nodes):
    if node in queue_q1:
        q1_minutes = sorted(queue_q1[node].keys())
        q1_avg = [sum(queue_q1[node][m])/len(queue_q1[node][m]) for m in q1_minutes]
        fig.add_trace(go.Scatter(x=q1_minutes, y=q1_avg,
                                 mode="lines+markers", name=f"Node {node} Q1",
                                 line=dict(color=fixed_colors[node], dash="solid"), yaxis="y1"))
    if node in queue_q2:
        q2_minutes = sorted(queue_q2[node].keys())
        q2_avg = [sum(queue_q2[node][m])/len(queue_q2[node][m]) for m in q2_minutes]
        fig.add_trace(go.Scatter(x=q2_minutes, y=q2_avg,
                                 mode="lines+markers", name=f"Node {node} Q2",
                                 line=dict(color=fixed_colors[node], dash="dot"), yaxis="y1"))

# Received trace
recv_df = pd.DataFrame({
    "Minute": list(recv_per_minute.keys()),
    "Received": list(recv_per_minute.values())
}).sort_values("Minute")
fig.add_trace(go.Scatter(x=recv_df["Minute"], y=recv_df["Received"],
                         mode="lines+markers", name="Messages Received (Node 16)",
                         line=dict(color=fixed_colors["received"], width=3), yaxis="y2"))

# === LAYOUT ===
success = (total_received / total_sent * 100) if total_sent > 0 else 0
fig.update_layout(
    title="Queue Fill (Q1/Q2) for Selected Nodes + Received Messages",
    xaxis=dict(title="Time (minutes)"),
    yaxis=dict(title=f"Queue Fill (0–{queue_size})", side="left"),
    yaxis2=dict(title="Messages Received", overlaying="y", side="right"),
    legend_title_text="Legend",
    template="plotly_white",
    height=700,
    annotations=[
        dict(
            xref='paper', yref='paper',
            x=0.1, y=1.1,
            xanchor='left', yanchor='top',
            text=f"📦 Sent: {total_sent} | ✅ Received: {total_received} | 📈 Success rate: {success:.1f}%",
            showarrow=False,
            font=dict(size=14)
        )
    ]
)

fig.show()
