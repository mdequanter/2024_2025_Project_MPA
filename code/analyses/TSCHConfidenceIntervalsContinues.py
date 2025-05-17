import pandas as pd
import scipy.stats as stats
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# === Load the CSV file ===
df = pd.read_csv("code/analyses/tsch_summary_means.csv")
df["Timing"] = df["File"].str.extract(r"TSCH_(\d+)_")[0].astype(int)

# Compute messages per minute
df["Msgs/min"] = (60 / df["Timing"]).round(0)

# === Compute confidence intervals ===
def compute_ci(series):
    n = len(series)
    mean = series.mean()
    h = stats.sem(series) * stats.t.ppf(0.975, n - 1) if n > 1 else 0
    return mean, h

# === Group and compute CI per msgs/min ===
records = []
for msgs_per_minute, group in df.groupby("Msgs/min"):
    lat_mean, lat_ci = compute_ci(group["End-to-End latency(ms)"])
    thr_mean, thr_ci = compute_ci(group["Throughput %"])
    bit_mean, bit_ci = compute_ci(group["Sendrate (Bps)"])
    records.append({
        "Msgs/min": msgs_per_minute,
        "Latency Mean": lat_mean,
        "Latency Upper": lat_mean + lat_ci,
        "Latency Lower": lat_mean - lat_ci,
        "Throughput Mean": thr_mean,
        "Throughput Upper": thr_mean + thr_ci,
        "Throughput Lower": thr_mean - thr_ci,
        "Bitrate Mean": bit_mean * 8,
        "Bitrate Upper": (bit_mean + bit_ci) * 8,
        "Bitrate Lower": (bit_mean - bit_ci) * 8,
    })

# Convert to DataFrame and sort
ci_df = pd.DataFrame(records).sort_values("Msgs/min")

# === Create subplots ===
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

# === LATENCY PLOT ===
fig.add_trace(go.Scatter(
    x=ci_df["Msgs/min"], y=ci_df["Latency Upper"],
    line=dict(width=0),
    showlegend=False,
    hoverinfo='skip',
    name="Latency Upper",
), row=1, col=1)

fig.add_trace(go.Scatter(
    x=ci_df["Msgs/min"], y=ci_df["Latency Lower"],
    fill='tonexty',
    fillcolor='rgba(65, 105, 225, 0.2)',  # royalblue semi-transparent
    line=dict(width=0),
    hoverinfo='skip',
    name="Latency CI",
    showlegend=False
), row=1, col=1)

fig.add_trace(go.Scatter(
    x=ci_df["Msgs/min"], y=ci_df["Latency Mean"],
    mode='lines+markers',
    line=dict(color='royalblue'),
    name="Latency Mean"
), row=1, col=1)

# === THROUGHPUT PLOT ===
fig.add_trace(go.Scatter(
    x=ci_df["Msgs/min"], y=ci_df["Throughput Upper"],
    line=dict(width=0),
    showlegend=False,
    hoverinfo='skip',
), row=2, col=1)

fig.add_trace(go.Scatter(
    x=ci_df["Msgs/min"], y=ci_df["Throughput Lower"],
    fill='tonexty',
    fillcolor='rgba(46, 139, 87, 0.2)',  # seagreen semi-transparent
    line=dict(width=0),
    hoverinfo='skip',
    showlegend=False
), row=2, col=1)

fig.add_trace(go.Scatter(
    x=ci_df["Msgs/min"], y=ci_df["Throughput Mean"],
    mode='lines+markers',
    line=dict(color='seagreen'),
    name="Throughput Mean"
), row=2, col=1)

# === BITRATE PLOT ===
fig.add_trace(go.Scatter(
    x=ci_df["Msgs/min"], y=ci_df["Bitrate Upper"],
    line=dict(width=0),
    showlegend=False,
    hoverinfo='skip',
), row=3, col=1)

fig.add_trace(go.Scatter(
    x=ci_df["Msgs/min"], y=ci_df["Bitrate Lower"],
    fill='tonexty',
    fillcolor='rgba(255, 140, 0, 0.2)',  # darkorange semi-transparent
    line=dict(width=0),
    hoverinfo='skip',
    showlegend=False
), row=3, col=1)

fig.add_trace(go.Scatter(
    x=ci_df["Msgs/min"], y=ci_df["Bitrate Mean"],
    mode='lines+markers',
    line=dict(color='darkorange'),
    name="Bitrate Mean"
), row=3, col=1)

# === Final layout ===
fig.update_layout(
    title="95% Confidence Intervals by Send Rate (TSCH)",
    height=750,
    template="plotly_white",
    font=dict(size=16),
    title_font=dict(size=22),
    showlegend=False
)

fig.update_xaxes(title_text="Send Rate (messages/min)", row=3, col=1, title_font=dict(size=18), tickfont=dict(size=14))
fig.update_yaxes(title_text="Latency (ms)", row=1, col=1, title_font=dict(size=18), tickfont=dict(size=14))
fig.update_yaxes(title_text="PDR (%)", row=2, col=1, title_font=dict(size=18), tickfont=dict(size=14))
fig.update_yaxes(title_text="Throughput (bits/s)", row=3, col=1, title_font=dict(size=18), tickfont=dict(size=14))

fig.show()
