import pandas as pd
import scipy.stats as stats
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# === Load the CSV file ===
df = pd.read_csv("code/analyses/csma_summary_means.csv")
df["Timing"] = df["File"].str.extract(r"CSMA_([\d\.]+)_")[0].astype(float)

# Compute messages per minute
df["Msgs/min"] = (60 / df["Timing"]).round(2)  # Inverse of timing (e.g., 0.1 → 600 msg/min)

# === Compute confidence intervals ===
def compute_ci(series):
    n = len(series)
    mean = series.mean()
    h = stats.sem(series) * stats.t.ppf(0.975, n - 1) if n > 1 else 0
    return round(mean, 2), round(h, 2)

# === Group and compute CI per messages/min ===
records = []
for msgs_per_minute, group in df.groupby("Msgs/min"):
    lat_mean, lat_ci = compute_ci(group["End-to-End latency(ms)"])
    thr_mean, thr_ci = compute_ci(group["Throughput %"])
    records.append({
        "Msgs/min": msgs_per_minute,
        "Latency Mean": lat_mean,
        "Latency CI": lat_ci,
        "Throughput Mean": thr_mean,
        "Throughput CI": thr_ci
    })

# Convert to DataFrame and sort
ci_df = pd.DataFrame(records).sort_values("Msgs/min")
ci_df["Msgs/min"] = ci_df["Msgs/min"].astype(str)  # Use as categorical labels

# === Create subplot with two rows ===
fig = make_subplots(
    rows=2, cols=1,
    shared_xaxes=False,
    subplot_titles=[
        "End-to-End Latency per Send Rate (msgs/min)",
        "Throughput (%) per Send Rate (msgs/min)"
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

# === Final layout ===
fig.update_layout(
    title="95% Confidence Intervals by Send Rate (CSMA)",
    height=1200,
    template="plotly_white",
    showlegend=False
)

# Force categorical x-axis and normal formatting
fig.update_xaxes(title_text="Send Rate (messages/min)", type="category", row=1, col=1)
fig.update_xaxes(title_text="Send Rate (messages/min)", type="category", row=2, col=1)
fig.update_yaxes(title_text="Latency (ms)", tickformat=".2f", row=1, col=1)
fig.update_yaxes(title_text="Throughput (%)", tickformat=".2f", row=2, col=1)

fig.show()
