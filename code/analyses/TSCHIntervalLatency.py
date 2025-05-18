import pandas as pd
import scipy.stats as stats
import plotly.graph_objects as go

# === Load CSV ===
df = pd.read_csv("code/analyses/tsch_summary_stats.csv")
df["Timing"] = df["File"].str.extract(r"TSCH_(\d+)_")[0].astype(int)

# === Compute messages per minute ===
df["Msgs/min"] = (60 / df["Timing"]).round(0)

# === Compute statistics ===
def compute_stats(series):
    n = len(series)
    mean = series.mean()
    h = stats.sem(series) * stats.t.ppf(0.975, n - 1) if n > 1 else 0
    return {
        "mean": mean,
        "ci_upper": mean + h,
        "ci_lower": mean - h,
        "median": series.median(),
        "min": series.min(),
        "max": series.max()
    }

# === Aggregate per Msgs/min group ===
records = []
for msgs_per_minute, group in df.groupby("Msgs/min"):
    lat = compute_stats(group["Latency Mean (ms)"])
    records.append({
        "Msgs/min": msgs_per_minute,
        "Mean": lat["mean"],
        "CI Lower": lat["ci_lower"],
        "CI Upper": lat["ci_upper"],
        "Median": lat["median"],
        "Min": lat["min"],
        "Max": lat["max"]
    })

ci_df = pd.DataFrame(records).sort_values("Msgs/min")

# === Create Latency Plot ===
fig = go.Figure()

# Confidence interval area
fig.add_trace(go.Scatter(
    x=ci_df["Msgs/min"], y=ci_df["CI Upper"],
    line=dict(width=0),
    hoverinfo='skip',
    showlegend=False
))
fig.add_trace(go.Scatter(
    x=ci_df["Msgs/min"], y=ci_df["CI Lower"],
    fill='tonexty',
    fillcolor='rgba(65, 105, 225, 0.2)',
    line=dict(width=0),
    hoverinfo='skip',
    name="95% CI"
))

# Mean line
fig.add_trace(go.Scatter(
    x=ci_df["Msgs/min"], y=ci_df["Mean"],
    mode='lines+markers',
    line=dict(color='royalblue'),
    name="Mean"
))

# Median line
fig.add_trace(go.Scatter(
    x=ci_df["Msgs/min"], y=ci_df["Median"],
    mode='lines',
    line=dict(color='black', dash='dash'),
    name="Median"
))

# Min line
fig.add_trace(go.Scatter(
    x=ci_df["Msgs/min"], y=ci_df["Min"],
    mode='lines',
    line=dict(color='grey', dash='dot'),
    name="Min"
))

# Max line
fig.add_trace(go.Scatter(
    x=ci_df["Msgs/min"], y=ci_df["Max"],
    mode='lines',
    line=dict(color='darkgrey', dash='dot'),
    name="Max"
))

# === Layout ===
fig.update_layout(
    title="End-to-End Latency by Send Rate (TSCH)",
    template="plotly_white",
    font=dict(size=16),
    title_font=dict(size=22),
    xaxis_title="Send Rate (messages/min)",
    yaxis_title="Latency (ms)",
    legend_title="Metric"
)

# Force x-axis ticks every 5 units
fig.update_xaxes(
    tickmode='linear',
    dtick=5,
    tickfont=dict(size=14)
)
fig.update_yaxes(tickfont=dict(size=14))

fig.show()
