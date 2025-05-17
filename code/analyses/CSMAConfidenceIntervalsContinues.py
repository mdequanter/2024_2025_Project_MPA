import pandas as pd
import scipy.stats as stats
import plotly.graph_objects as go

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

# === Group and calculate bitrate (throughput) only ===
records = []
for msgs_per_minute, group in df.groupby("Msgs/min"):
    bit_mean, bit_ci = compute_ci(group["Sendrate (Bps)"])
    records.append({
        "Msgs/min": msgs_per_minute,
        "Bitrate Mean": bit_mean * 8,
        "Bitrate Upper": (bit_mean + bit_ci) * 8,
        "Bitrate Lower": (bit_mean - bit_ci) * 8,
    })

ci_df = pd.DataFrame(records).sort_values("Msgs/min")

# === Create Bitrate Plot ===
fig = go.Figure()

# Confidence interval (shaded area)
fig.add_trace(go.Scatter(
    x=ci_df["Msgs/min"], y=ci_df["Bitrate Upper"],
    line=dict(width=0),
    hoverinfo='skip',
    showlegend=False
))
fig.add_trace(go.Scatter(
    x=ci_df["Msgs/min"], y=ci_df["Bitrate Lower"],
    fill='tonexty',
    fillcolor='rgba(255, 140, 0, 0.2)',  # darkorange semi-transparent
    line=dict(width=0),
    hoverinfo='skip',
    showlegend=False
))

# Bitrate mean line
fig.add_trace(go.Scatter(
    x=ci_df["Msgs/min"], y=ci_df["Bitrate Mean"],
    mode='lines+markers',
    line=dict(color='darkorange'),
    name="Throughput (bits/s)"
))

# === Layout ===
fig.update_layout(
    title="Throughput (bits/s) with 95% Confidence Interval (CSMA)",
    height=450,
    template="plotly_white",
    showlegend=False,
    font=dict(size=16),
    title_font=dict(size=22)
)

fig.update_xaxes(
    title_text="Send Rate (messages/min)",
    title_font=dict(size=18),
    tickfont=dict(size=14),
    tickmode='linear',
    dtick=20
)

fig.update_yaxes(
    title_text="Throughput (bits/s)",
    title_font=dict(size=18),
    tickfont=dict(size=14),
    tickformat=".2f"
)

fig.show()
