import pandas as pd
import scipy.stats as stats
import plotly.graph_objects as go
from plotly.subplots import make_subplots

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
    lat = compute_stats(group["Latency Mean (ms)"])
    thr = compute_stats(group["Throughput % Mean"])
    bit = compute_stats(group["Sendrate Mean (Bps)"])

    records.append({
        "Msgs/min": msgs_per_minute,
        **{f"Latency {k.title()}": v for k, v in lat.items()},
        **{f"Throughput {k.title()}": v for k, v in thr.items()},
        **{f"Bitrate {k.title()}": v * 8 for k, v in bit.items()},  # Bps to bits/s
    })

ci_df = pd.DataFrame(records).sort_values("Msgs/min")

# === Plot setup ===
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

# === Helper function ===
def add_stats_traces(fig, row, x, stats_dict, color, name):
    # Confidence Interval area
    fig.add_trace(go.Scatter(
        x=x, y=stats_dict["Ci_Upper"],
        line=dict(width=0),
        hoverinfo='skip',
        showlegend=False
    ), row=row, col=1)

    fig.add_trace(go.Scatter(
        x=x, y=stats_dict["Ci_Lower"],
        fill='tonexty',
        fillcolor=color,
        line=dict(width=0),
        hoverinfo='skip',
        showlegend=False
    ), row=row, col=1)

    # Mean
    fig.add_trace(go.Scatter(
        x=x, y=stats_dict["Mean"],
        mode='lines+markers',
        line=dict(color=color.replace("0.2", "1.0")),
        name=f"{name} Mean"
    ), row=row, col=1)

    # Median
    fig.add_trace(go.Scatter(
        x=x, y=stats_dict["Median"],
        mode='lines',
        line=dict(color='black', dash='dash'),
        name=f"{name} Median"
    ), row=row, col=1)

    # Min
    fig.add_trace(go.Scatter(
        x=x, y=stats_dict["Min"],
        mode='lines',
        line=dict(color='grey', dash='dot'),
        name=f"{name} Min"
    ), row=row, col=1)

    # Max
    fig.add_trace(go.Scatter(
        x=x, y=stats_dict["Max"],
        mode='lines',
        line=dict(color='darkgrey', dash='dot'),
        name=f"{name} Max"
    ), row=row, col=1)

# === Add all three metrics ===
add_stats_traces(
    fig, row=1, x=ci_df["Msgs/min"],
    stats_dict={
        "Mean": ci_df["Latency Mean"],
        "Ci_Lower": ci_df["Latency Ci_Lower"],
        "Ci_Upper": ci_df["Latency Ci_Upper"],
        "Median": ci_df["Latency Median"],
        "Min": ci_df["Latency Min"],
        "Max": ci_df["Latency Max"]
    },
    color='rgba(65, 105, 225, 0.2)',
    name="Latency"
)

add_stats_traces(
    fig, row=2, x=ci_df["Msgs/min"],
    stats_dict={
        "Mean": ci_df["Throughput Mean"],
        "Ci_Lower": ci_df["Throughput Ci_Lower"],
        "Ci_Upper": ci_df["Throughput Ci_Upper"],
        "Median": ci_df["Throughput Median"],
        "Min": ci_df["Throughput Min"],
        "Max": ci_df["Throughput Max"]
    },
    color='rgba(46, 139, 87, 0.2)',
    name="Throughput"
)

add_stats_traces(
    fig, row=3, x=ci_df["Msgs/min"],
    stats_dict={
        "Mean": ci_df["Bitrate Mean"],
        "Ci_Lower": ci_df["Bitrate Ci_Lower"],
        "Ci_Upper": ci_df["Bitrate Ci_Upper"],
        "Median": ci_df["Bitrate Median"],
        "Min": ci_df["Bitrate Min"],
        "Max": ci_df["Bitrate Max"]
    },
    color='rgba(255, 140, 0, 0.2)',
    name="Bitrate"
)

# === Final layout ===
fig.update_layout(
    title="TSCH Stats: CI + Min/Max + Median + Mean",
    height=850,
    template="plotly_white",
    font=dict(size=16),
    title_font=dict(size=22),
    showlegend=True
)

fig.update_xaxes(title_text="Send Rate (messages/min)", row=3, col=1, title_font=dict(size=18), tickfont=dict(size=14))
fig.update_yaxes(title_text="Latency (ms)", row=1, col=1, title_font=dict(size=18), tickfont=dict(size=14))
fig.update_yaxes(title_text="PDR (%)", row=2, col=1, title_font=dict(size=18), tickfont=dict(size=14))
fig.update_yaxes(title_text="Throughput (bits/s)", row=3, col=1, title_font=dict(size=18), tickfont=dict(size=14))

fig.show()
