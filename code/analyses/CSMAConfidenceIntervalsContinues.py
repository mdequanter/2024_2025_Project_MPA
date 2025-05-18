import pandas as pd
import scipy.stats as stats
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# === Load CSV ===
df = pd.read_csv("code/analyses/csma_summary_means.csv")
df["Timing"] = df["File"].str.extract(r"CSMA_([\d\.]+)_")[0].astype(float)
df["Msgs/min"] = (60 / df["Timing"]).round(2)

# === Compute confidence intervals ===
def compute_ci(series):
    n = len(series)
    mean = series.mean()
    h = stats.sem(series) * stats.t.ppf(0.975, n - 1) if n > 1 else 0
    return mean, h

# === Group and calculate metrics ===
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

# === LATENCY ===
fig.add_trace(go.Scatter(
    x=ci_df["Msgs/min"], y=ci_df["Latency Upper"],
    line=dict(width=0), hoverinfo='skip', showlegend=False
), row=1, col=1)
fig.add_trace(go.Scatter(
    x=ci_df["Msgs/min"], y=ci_df["Latency Lower"],
    fill='tonexty',
    fillcolor='rgba(65, 105, 225, 0.2)',
    line=dict(width=0), hoverinfo='skip', showlegend=False
), row=1, col=1)
fig.add_trace(go.Scatter(
    x=ci_df["Msgs/min"], y=ci_df["Latency Mean"],
    mode='lines+markers', line=dict(color='royalblue'),
    name="Latency"
), row=1, col=1)

# === THROUGHPUT ===
fig.add_trace(go.Scatter(
    x=ci_df["Msgs/min"], y=ci_df["Throughput Upper"],
    line=dict(width=0), hoverinfo='skip', showlegend=False
), row=2, col=1)
fig.add_trace(go.Scatter(
    x=ci_df["Msgs/min"], y=ci_df["Throughput Lower"],
    fill='tonexty',
    fillcolor='rgba(46, 139, 87, 0.2)',
    line=dict(width=0), hoverinfo='skip', showlegend=False
), row=2, col=1)
fig.add_trace(go.Scatter(
    x=ci_df["Msgs/min"], y=ci_df["Throughput Mean"],
    mode='lines+markers', line=dict(color='seagreen'),
    name="Throughput"
), row=2, col=1)

# === BITRATE ===
fig.add_trace(go.Scatter(
    x=ci_df["Msgs/min"], y=ci_df["Bitrate Upper"],
    line=dict(width=0), hoverinfo='skip', showlegend=False
), row=3, col=1)
fig.add_trace(go.Scatter(
    x=ci_df["Msgs/min"], y=ci_df["Bitrate Lower"],
    fill='tonexty',
    fillcolor='rgba(255, 140, 0, 0.2)',
    line=dict(width=0), hoverinfo='skip', showlegend=False
), row=3, col=1)
fig.add_trace(go.Scatter(
    x=ci_df["Msgs/min"], y=ci_df["Bitrate Mean"],
    mode='lines+markers', line=dict(color='darkorange'),
    name="Bitrate"
), row=3, col=1)

# === Layout ===
fig.update_layout(
    title="95% Confidence Intervals by Send Rate (CSMA)",
    height=1100,
    template="plotly_white",
    showlegend=False,
    font=dict(size=16),
    title_font=dict(size=22)
)

fig.update_xaxes(
    title_text="Send Rate (messages/min)", row=3, col=1,
    title_font=dict(size=18), tickfont=dict(size=14)
)
fig.update_yaxes(
    title_text="Latency (ms)", row=1, col=1,
    title_font=dict(size=18), tickfont=dict(size=14), tickformat=".2f"
)
fig.update_yaxes(
    title_text="PDR (%)", row=2, col=1,
    title_font=dict(size=18), tickfont=dict(size=14), tickformat=".2f"
)
fig.update_yaxes(
    title_text="Throughput (bits/s)", row=3, col=1,
    title_font=dict(size=18), tickfont=dict(size=14), tickformat=".2f"
)

fig.show()