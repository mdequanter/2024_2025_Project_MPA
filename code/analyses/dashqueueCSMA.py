import re
from collections import defaultdict
import pandas as pd
import plotly.graph_objects as go
import argparse

# === CLI Argument Configuration ===
parser = argparse.ArgumentParser(description="Parse COOJA log and plot per-second metrics with latency.")
parser.add_argument("input_path", help="Path to the COOJA log file")
args = parser.parse_args()

logfile = args.input_path

# === Initialize data containers ===
sent_per_second = defaultdict(int)
received_per_second = defaultdict(int)
recv_bytes_per_second = defaultdict(int)
not_for_us_per_second = defaultdict(int)
queue_length_per_second = defaultdict(list)
latency_per_second = defaultdict(list)
sent_messages = {}

# === Parse the log file ===
with open(logfile, 'r') as file:
    for line in file:
        tick_match = re.match(r'^(\d+)', line)
        if not tick_match:
            continue
        tick = int(tick_match.group(1))
        second = tick // 1_000_000

        # Detect sent message
        send_match = re.match(r'^\d+\s+(\d+)\s+Sending message: \'(.+?)\' to fd00::210:10:10:10', line)
        if send_match:
            sender = send_match.group(1)
            msg = send_match.group(2).strip()
            sent_messages[msg] = tick
            sent_per_second[second] += 1

        # Detect received message and map back to sent second
        recv_match = re.match(r'^(\d+)\s+16\s+Data received from .*? in (\d+) hops with datalength \d+: \'(.+?)\'', line)
        if recv_match:
            recv_tick = int(recv_match.group(1))
            msg = recv_match.group(3).strip()

            if msg in sent_messages:
                sent_tick = sent_messages[msg]
                sent_sec = sent_tick // 1_000_000
                latency_ms = (recv_tick - sent_tick) / 1000
                received_per_second[sent_sec] += 1
                recv_bytes_per_second[sent_sec] += len(msg)
                latency_per_second[sent_sec].append(latency_ms)

        # Detect "not for us"
        not_for_us_match = re.match(r'^\d+\s+(\d+)\s+\[WARN: CSMA\s+\]\s+not for us', line)
        if not_for_us_match:
            not_for_us_per_second[second] += 1

        # Detect queue length
        queue_match = re.search(r'queue length (\d+)', line)
        if queue_match:
            queue_len = int(queue_match.group(1))
            queue_length_per_second[second].append(queue_len)

# === Build DataFrame ===
all_seconds = sorted(set(sent_per_second) |
                     set(received_per_second) |
                     set(not_for_us_per_second) |
                     set(queue_length_per_second))

records = []
for second in all_seconds:
    sent = sent_per_second.get(second, 0)
    recv = received_per_second.get(second, 0)
    success = (recv / sent * 100) if sent > 0 else 0
    datarate = recv_bytes_per_second.get(second, 0)
    not_for_us = not_for_us_per_second.get(second, 0)
    queue_max = max(queue_length_per_second[second]) if queue_length_per_second[second] else 0
    avg_latency = sum(latency_per_second[second]) / len(latency_per_second[second]) if latency_per_second[second] else 0

    records.append({
        "Second": second,
        "Sent": sent,
        "Received": recv,
        "Throughput %": success,
        "Datarate (Bps)": datarate,
        "Not-for-us": not_for_us,
        "Queue Length": queue_max,
        "End-to-End latency(ms)": avg_latency
    })

df = pd.DataFrame(records)

# === Plotly Chart ===
fig = go.Figure()
fig.add_trace(go.Scatter(x=df["Second"], y=df["Sent"], mode='lines+markers', name='Sent messages'))
fig.add_trace(go.Scatter(x=df["Second"], y=df["Received"], mode='lines+markers', name='Received messages'))
fig.add_trace(go.Scatter(x=df["Second"], y=df["Throughput %"], mode='lines+markers', name='Throughput %'))
fig.add_trace(go.Scatter(x=df["Second"], y=df["Datarate (Bps)"], mode='lines+markers', name='Datarate (Bps)'))
fig.add_trace(go.Scatter(x=df["Second"], y=df["Not-for-us"], mode='lines+markers', name='Not-for-us count'))
fig.add_trace(go.Scatter(x=df["Second"], y=df["Queue Length"], mode='lines+markers', name='Queue Length'))
fig.add_trace(go.Scatter(x=df["Second"], y=df["End-to-End latency(ms)"], mode='lines+markers', name='End-to-End latency(ms)'))

# === Summary ===
total_sent = sum(sent_per_second.values())
total_recv = sum(received_per_second.values())
overall_success = (total_recv / total_sent * 100) if total_sent > 0 else 0

fig.update_layout(
    title=f"Per-second Transmission Statistics with Latency ({logfile})",
    xaxis_title="Second",
    yaxis_title="Values",
    legend_title="Metric",
    template="plotly_white",
    height=650,
    annotations=[
        dict(
            xref='paper', yref='paper',
            x=0.01, y=1.05,
            xanchor='left', yanchor='bottom',
            text=(
                f"📦 Sent: <b>{total_sent}</b> | "
                f"✅ Received: <b>{total_recv}</b> | "
                f"📈 Success rate: <b>{overall_success:.1f}%</b>"
            ),
            showarrow=False,
            font=dict(size=18)
        )
    ]
)

fig.show()
