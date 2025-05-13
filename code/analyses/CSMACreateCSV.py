import os
import re
import csv
from collections import defaultdict
import pandas as pd

# === Configuration ===
log_dir = "code/analyses/logfiles"  # Directory with CSMA_*.testlog files
output_csv = "code/analyses/csma_summary_means.csv"

# === Initialize list for summary rows
summary_records = []

# === List all CSMA log files
log_files = [f for f in os.listdir(log_dir) if f.startswith("CSMA_") and f.endswith(".testlog")]

# === Process each file
for filename in log_files:
    filepath = os.path.join(log_dir, filename)

    sent_messages = {}
    sender_delays = defaultdict(list)
    sent_counts = defaultdict(int)
    recv_counts = defaultdict(int)
    recv_bytes = defaultdict(int)
    first_send_time = defaultdict(lambda: float('inf'))
    last_recv_time = defaultdict(lambda: 0)

    with open(filepath, 'r') as file:
        lines = file.readlines()

    for line in lines:
        # Sent line
        send_match = re.match(r'^(\d+)\s+(\d+)\s+Sending message: \'(.+?)\' to fd00::210:10:10:10', line)
        if send_match:
            tick = int(send_match.group(1))
            node = send_match.group(2)
            msg = send_match.group(3).strip()
            sent_messages[msg] = (tick, node)
            sent_counts[node] += 1
            first_send_time[node] = min(first_send_time[node], tick)

        # Received line
        recv_match = re.match(r'^(\d+)\s+16\s+Data received from .*? in \d+ hops with datalength \d+: \'(.+?)\'', line)
        if recv_match:
            tick = int(recv_match.group(1))
            msg = recv_match.group(2).strip()
            if msg in sent_messages:
                send_tick, node = sent_messages[msg]
                delay = tick - send_tick
                sender_delays[node].append(delay)
                recv_counts[node] += 1
                recv_bytes[node] += len(msg)
                last_recv_time[node] = max(last_recv_time[node], tick)

    # === Compute per-file means ===
    total_sent = total_recv = total_delay = total_throughput = 0
    num_senders = 0

    for node in sent_counts:
        sent = sent_counts[node]
        received = recv_counts[node]
        if received > 0:
            delay = sum(sender_delays[node]) / (received*1000)
            timespan = (last_recv_time[node] - first_send_time[node]) / 1000  # ms → sec
            throughput = (recv_bytes[node] / (timespan / 1000)) if timespan > 0 else 0

            total_sent += sent
            total_recv += received
            total_delay += delay
            total_throughput += throughput
            num_senders += 1

    if num_senders > 0 and total_sent > 0:
        summary_records.append({
            "File": filename,
            "End-to-End latency(ms)": round(total_delay / num_senders, 2),
            "Sent": total_sent // num_senders,
            "Received": total_recv // num_senders,
            "Throughput %": round((total_recv / total_sent) * 100, 2),
            "Sendrate (Bps)": round(total_throughput / num_senders, 2)
        })

# === Write to CSV
os.makedirs(os.path.dirname(output_csv), exist_ok=True)
df = pd.DataFrame(summary_records)
df.to_csv(output_csv, index=False)

print(f"✅ Summary saved to: {output_csv}")
