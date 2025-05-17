import re
import pandas as pd
import plotly.express as px
from collections import defaultdict
import argparse

# === Configuration ===
parser = argparse.ArgumentParser(description="Parse COOJA test log.")
parser.add_argument("input_path", help="Path to the COOJA log file")
args = parser.parse_args()

logfile = args.input_path

sender_nodes = [10, 11, 19, 2, 20, 21, 22, 23, 24, 25, 26, 27, 28, 3, 4, 5, 6, 7, 8, 9]

# === Parse log and collect counts ===
send_counts = defaultdict(lambda: defaultdict(int))  # node -> minute -> count
total_per_minute = defaultdict(int)  # minute -> total sends from all nodes

with open(logfile, 'r') as file:
    for line in file:
        match = re.match(r'^(\d+)\s+(\d+)\s+Sending message: ', line)
        if match:
            tick = int(match.group(1))
            node = int(match.group(2))
            if node in sender_nodes:
                minute = int(tick / 1_000_000 // 60)
                send_counts[node][minute] += 1
                total_per_minute[minute] += 1

# === Build DataFrame ===
records = []
max_minute = max(total_per_minute.keys(), default=0)

for minute in range(max_minute + 1):
    # Add total line
    total = total_per_minute.get(minute, 0)
    records.append({"Node": "Total", "Minute": minute, "Messages Sent": total})

    # Add each node's count (even if 0)
    for node in sender_nodes:
        count = send_counts[node].get(minute, 0)
        records.append({"Node": str(node), "Minute": minute, "Messages Sent": count})

df = pd.DataFrame(records)

# === Sort to ensure proper line rendering ===
df = df.sort_values(by=["Node", "Minute"])

# === Ensure categorical node sorting for consistent plot order ===
df["Node"] = pd.Categorical(df["Node"], ordered=True,
                            categories=[str(n) for n in sender_nodes] + ["Total"])

# === Plot ===
fig = px.line(
    df,
    x="Minute",
    y="Messages Sent",
    color="Node",
    title="Messages Sent per Minute per Node (with Total)",
    labels={"Minute": "Time (minutes)", "Messages Sent": "Messages Sent"},
    line_group="Node",
    markers=True  # Add markers to ensure even sparse data is visible
)

# Make "Total" line black and bold
fig.for_each_trace(lambda t: t.update(line=dict(width=4, color='black')) if t.name == "Total" else ())

fig.update_layout(legend_title_text="Node ID")
fig.show()
