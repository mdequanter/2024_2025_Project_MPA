import pandas as pd
import scipy.stats as stats
import plotly.graph_objects as go

# === Load the CSV file ===
df = pd.read_csv("code/analyses/tsch_summary_stats.csv")  # must contain min/max/median
df["Timing"] = df["File"].str.extract(r"TSCH_(\d+)_")[0].astype(int)

# Compute messages per minute
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

# === Group and compute stats per msgs/min ===
records = []
for msgs_per_minute, group in df.groupby("Msgs/min"):
    thr = compute_stats(group["Throughput % Mean"])
    records.append({
        "Msgs/min": msgs_per_minute,
        **{f"Throughput {k.title()}": v for k, v in thr.items()},
    })

ci_df = pd.DataFrame(records).sort_values("Msgs/min")

# === PDR Plot ===
fig = go.Figure()

# Confidence Interval (shaded)
fig.add_trace(go.Scatter(
    x=ci_df["Msgs/min"], y=ci_df["Throughput Ci_Upper"],
    line=dict(width=0),
    hoverinfo='skip',
    showlegend=False
))
fig.add_trace(go.Scatter(
    x=ci_df["Msgs/min"], y=ci_df["Throughput Ci_Lower"],
    fill='tonexty',
    fillcolor='rgba(46, 139, 87, 0.2)',
    line=dict(width=0),
    hoverinfo='skip',
    name="95% CI"
))

# Mean line
fig.add_trace(go.Scatter(
    x=ci_df["Msgs/min"], y=ci_df["Throughput Mean"],
    mode='lines+markers',
    line=dict(color='seagreen'),
    name="Mean"
))

# Median line
fig.add_trace(go.Scatter(
    x=ci_df["Msgs/min"], y=ci_df["Throughput Median"],
    mode='lines',
    line=dict(color='black', dash='dash'),
    name="Median"
))

# Min line
fig.add_trace(go.Scatter(
    x=ci_df["Msgs/min"], y=ci_df["Throughput Min"],
    mode='lines',
    line=dict(color='grey', dash='dot'),
    name="Min"
))

# Max line
fig.add_trace(go.Scatter(
    x=ci_df["Msgs/min"], y=ci_df["Throughput Max"],
    mode='lines',
    line=dict(color='darkgrey', dash='dot'),
    name="Max"
))

# === Layout ===
fig.update_layout(
    title="TSCH PDR (%) by Send Rate ",
    template="plotly_white",
    font=dict(size=16),
    title_font=dict(size=22),
    xaxis_title="Send Rate (messages/min)",
    yaxis_title="PDR (%)",
    legend_title="Metric"
)

fig.update_xaxes(tickfont=dict(size=14))
fig.update_yaxes(tickfont=dict(size=14))


fig.update_xaxes(
    tickmode='linear',
    dtick=5,
    title_text="Send Rate (messages/min)",
    tickfont=dict(size=14)
)


fig.show()
