import pandas as pd
import scipy.stats as stats
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# === Load the CSV file ===
df = pd.read_csv("code/analyses/tsch_summary_means.csv")
df["Timing"] = df["File"].str.extract(r"TSCH_(\d+)_")[0].astype(int)

# Compute messages per minute
df["Msgs/min"] = (60 / df["Timing"]).round(2)

# === Compute confidence intervals ===
def compute_ci(series):
    n = len(series)
    mean = series.mean()
    h = stats.sem(series) * stats.t.ppf(0.975, n - 1) if n > 1 else 0
    return round(mean, 2), round(h, 2)

# === Group and compute CI per msgs/min ===
records = []
for msgs_per_minute, group in df.groupby("Msgs/min"):
    lat_mean, lat_ci = compute_ci(group["End-to-End latency(ms)"])
    thr_mean, thr_ci = compute_ci(group["Throughput %"])
    bit_mean, bit_ci = compute_ci(group["Sendrate (Bps)"])
    records.append({
        "Msgs/min": msgs_per_minute,
        "Latency Mean": lat_mean,
        "Latency CI": lat_ci,
        "Throughput Mean": thr_mean,
        "Throughput CI": thr_ci,
        "Bitrate Mean": bit_mean*8,
        "Bitrate CI": bit_ci*8,  # Convert to bits
    })

# Convert to DataFrame and sort
ci_df = pd.DataFrame(records).sort_values("Msgs/min")
ci_df["Msgs/min"] = ci_df["Msgs/min"].astype(str)  # force categorical for x-axis

# === Create subplot with two rows ===
fig = make_subplots(
    rows=3, cols=1,
    shared_xaxes=True,
    vertical_spacing=0.12,
    subplot_titles=[
        "End-to-End Latency per Send Rate (msgs/min)",
        "Throughput (%) per Send Rate (msgs/min)",
        "Bitrate (bits/s) per Send Rate (msgs/min)"
    ]
)

# === Latency subplot ===
fig.add_trace(go.Bar(
    x=ci_df["Msgs/min"],
    y=ci_df["Latency Mean"],
    error_y=dict(type='data', array=ci_df["Latency CI"], visible=True),
    name="Latency",
    marker_color='royalblue'
), row=1, col=1)

# === Throughput subplot ===
fig.add_trace(go.Bar(
    x=ci_df["Msgs/min"],
    y=ci_df["Throughput Mean"],
    error_y=dict(type='data', array=ci_df["Throughput CI"], visible=True),
    name="Throughput",
    marker_color='seagreen'
), row=2, col=1)

# === Bitrate subplot ===
fig.add_trace(go.Bar(
    x=ci_df["Msgs/min"],
    y=ci_df["Bitrate Mean"],
    error_y=dict(type='data', array=ci_df["Bitrate CI"], visible=True),
    name="Bitrate",
    marker_color='darkorange'
), row=3, col=1)

# === Final layout with larger font ===
fig.update_layout(
    title="95% Confidence Intervals by Send Rate (TSCH)",
    height=750,
    template="plotly_white",
    showlegend=False,
    font=dict(size=16),  # <-- Larger font for all text
    title_font=dict(size=22),
)

# === Axis formatting ===
fig.update_xaxes(title_text="Send Rate (messages/min)", type="category", row=3, col=1, title_font=dict(size=18), tickfont=dict(size=14))
fig.update_yaxes(title_text="Latency (ms)", tickformat=".2f", row=1, col=1, title_font=dict(size=18), tickfont=dict(size=14))
fig.update_yaxes(title_text="PDR (%)", tickformat=".2f", row=2, col=1, title_font=dict(size=18), tickfont=dict(size=14))
fig.update_yaxes(title_text="Troughput (bits/s)", tickformat=".2f", row=3, col=1, title_font=dict(size=18), tickfont=dict(size=14))

fig.show()
