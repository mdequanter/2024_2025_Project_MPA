import re
from collections import defaultdict
import pandas as pd
import plotly.graph_objects as go
import argparse

# === CLI Argument Configuration ===
parser = argparse.ArgumentParser(description="Parse COOJA log and plot Trickle resets per minute.")
parser.add_argument("input_path", help="Path to the COOJA log file")
args = parser.parse_args()

logfile = args.input_path

# === Initialize data containers ===
resets_per_minute = defaultdict(int)

# === Parse the log file ===
with open(logfile, 'r') as file:
    for line in file:
        if "Multicast DIS => reset DIO timer" in line:
            tick_match = re.match(r'^(\d+)', line)
            if tick_match:
                tick = int(tick_match.group(1))
                minute = (tick // 1_000_000) // 60
                resets_per_minute[minute] += 1

# === Build DataFrame ===
all_minutes = sorted(resets_per_minute.keys())
records = [{"Minute": minute, "Trickle Resets": resets_per_minute[minute]} for minute in all_minutes]
df = pd.DataFrame(records)

# === Plotly Chart ===
fig = go.Figure()
fig.add_trace(go.Scatter(x=df["Minute"], y=df["Trickle Resets"], mode='lines+markers', name='Trickle Resets'))

# === Summary ===
total_resets = sum(resets_per_minute.values())

fig.update_layout(
    title=f"Per-minute Trickle Timer Resets ({logfile})",
    xaxis_title="Minute",
    yaxis_title="Reset Count",
    legend_title="Metric",
    template="plotly_white",
    height=500,
    annotations=[
        dict(
            xref='paper', yref='paper',
            x=0.01, y=1.05,
            xanchor='left', yanchor='bottom',
            text=f"🔄 Total Resets: <b>{total_resets}</b>",
            showarrow=False,
            font=dict(size=16)
        )
    ]
)

fig.show()
