import pandas as pd

# === Load original CSV ===
df = pd.read_csv("code/analyses/tsch_summary20250513.csv")

# === Define grouping columns and metrics ===
group_cols = ["File", "Timing", "Batch"]
metrics = [
    "End-to-End latency(ms)",
    "Sent",
    "Confirmed",
    "Received",
    "Throughput %",
    "Sendrate (Bps)"
]

# === Group and calculate mean ===
mean_df = df.groupby(group_cols)[metrics].mean().reset_index()

# === Save result ===
mean_df.to_csv("code/analyses/tsch_summary_means_by_batch.csv", index=False)

print("✅ Saved grouped mean CSV to 'tsch_summary_means_by_batch.csv'")
print(mean_df.head())
