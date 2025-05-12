import pandas as pd
import plotly.graph_objects as go
from scipy.stats import sem, t
import glob
import os

# === Configuration ===
folder = "code/analyses/logfiles/"
pattern = os.path.join(folder, "TSCH_*_combined.csv")
csv_files = sorted(glob.glob(pattern))

if not csv_files:
    print("❌ No CSV files found. Please check the path or file naming convention.")
    exit()

# === Load and merge all files ===
all_data = []
for file in csv_files:
    try:
        timing = int(os.path.basename(file).split("_")[1])
        df = pd.read_csv(file)
        df["Timing"] = timing
        all_data.append(df)
    except Exception as e:
        print(f"⚠️ Skipped file: {file} due to error: {e}")

df_all = pd.concat(all_data, ignore_index=True)

# === Convert data types ===
df_all["Sent"] = df_all["Sent"].astype(int)
df_all["Confirmed Sent"] = df_all["Confirmed Sent"].astype(int)
df_all["Received"] = df_all["Received"].astype(int)

# === Define metrics ===
metrics = ["Sent", "Confirmed Sent", "Received"]
colors = {"Sent": "blue", "Confirmed Sent": "orange", "Received": "green"}

# === Compute mean and 95% CI per timing ===
def mean_ci(series):
    mean = series.mean()
    ci = sem(series) * t.ppf((1 + 0.95) / 2, len(series) - 1)
    return mean, ci

timings = sorted(df_all["Timing"].unique())
results = {metric: {"means": [], "cis": []} for metric in metrics}

for timing in timings:
    group = df_all[df_all["Timing"] == timing]
    for metric in metrics:
        mean, ci = mean_ci(group[metric])
        results[metric]["means"].append(mean)
        results[metric]["cis"].append(ci)

# === Plot bar chart ===
fig = go.Figure()
for metric in metrics:
    fig.add_trace(go.Bar(
        name=metric,
        x=timings,
        y=results[metric]["means"],
        error_y=dict(type="data", array=results[metric]["cis"]),
        marker_color=colors[metric]
    ))

fig.update_layout(
    title="TSCH Metrics per Timing with 95% Confidence Intervals",
    xaxis_title="Timing (ms between messages)",
    yaxis_title="Metric Value",
    barmode='group',
    template="plotly_white",
    height=600
)

fig.show()
