import os
import re
import csv
from collections import defaultdict

# === Configuration ===
log_dir = "code/analyses/logfiles"
output_csv = "code/analyses/tsch_summary_stats.csv"
sender_nodes = [str(n) for n in [10, 11, 19, 2, 20, 21, 22, 23, 24, 25, 26, 27, 28, 3, 4, 5, 6, 7, 8, 9]]

# === Prepare CSV output ===
with open(output_csv, mode='w', newline='') as csvfile:
    fieldnames = [
        "File",
        "Latency Mean (ms)", "Latency Median (ms)", "Latency Min (ms)", "Latency Max (ms)",
        "Throughput % Mean", "Throughput % Median", "Throughput % Min", "Throughput % Max",
        "Sendrate Mean (Bps)", "Sendrate Median (Bps)", "Sendrate Min (Bps)", "Sendrate Max (Bps)",
        "Sent", "Confirmed", "Received"
    ]
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    writer.writeheader()

    # === Loop over files ===
    for filename in sorted(os.listdir(log_dir)):
        if not filename.startswith("TSCH_") or not filename.endswith(".testlog"):
            continue

        file_path = os.path.join(log_dir, filename)

        # Reset stats
        sent_messages = {}
        sender_delays = defaultdict(list)
        sent_counts = defaultdict(int)
        confirmed_sent_counts = defaultdict(int)
        recv_counts = defaultdict(int)
        recv_bytes = defaultdict(int)
        first_send_time = defaultdict(lambda: float('inf'))
        last_recv_time = defaultdict(lambda: 0)

        try:
            with open(file_path, 'r') as file:
                lines = list(file)
        except:
            continue

        for i, line in enumerate(lines):
            send_match = re.match(r'^(\d+)\s+(\d+)\s+Sending message: \'(.+?)\' to fd00::210:10:10:10', line)
            if send_match:
                time = int(send_match.group(1))
                sender_node = send_match.group(2)
                message = send_match.group(3).strip()
                if sender_node in sender_nodes:
                    sent_counts[sender_node] += 1
                    sent_messages[message] = (time, sender_node)
                    first_send_time[sender_node] = min(first_send_time[sender_node], time)
                    for followup in lines[i+1:i+11]:
                        tsch_match = re.match(r'^\d+\s+' + sender_node + r'\s+\[INFO: TSCH\s+\] send packet to .*', followup)
                        if tsch_match:
                            confirmed_sent_counts[sender_node] += 1
                            break

            recv_match = re.match(r'^(\d+)\s+16\s+Data received from .*? in \d+ hops with datalength \d+: \'(.+?)\'', line)
            if recv_match:
                time = int(recv_match.group(1))
                message = recv_match.group(2).strip()
                if message in sent_messages:
                    send_time, sender_node = sent_messages[message]
                    if sender_node in sender_nodes:
                        delay = time - send_time
                        sender_delays[sender_node].append(delay)
                        recv_counts[sender_node] += 1
                        recv_bytes[sender_node] += len(message)
                        last_recv_time[sender_node] = max(last_recv_time[sender_node], time)

        # === Aggregate results for the file ===
        all_delays = []
        pdr_list = []
        throughput_list = []

        total_sent = total_confirmed = total_received = total_throughput = 0
        num_senders = 0

        for sender in sender_nodes:
            sent = sent_counts[sender]
            confirmed = confirmed_sent_counts[sender]
            received = recv_counts[sender]

            if confirmed > 0 and received > 0:
                delays_ms = [d / 1000 for d in sender_delays[sender]]
                all_delays.extend(delays_ms)

                pdr = (received / confirmed) * 100
                pdr_list.append(pdr)

                time_span = (last_recv_time[sender] - first_send_time[sender]) / 1000
                throughput = (recv_bytes[sender] / (time_span / 1000)) if time_span > 0 else 0
                throughput_list.append(throughput)

                total_sent += sent
                total_confirmed += confirmed
                total_received += received
                total_throughput += throughput
                num_senders += 1

        # === Compute stats ===
        def compute_stats(values):
            values = sorted(values)
            n = len(values)
            if n == 0:
                return 0.0, 0.0, 0.0, 0.0
            mean = sum(values) / n
            median = (values[n // 2 - 1] + values[n // 2]) / 2 if n % 2 == 0 else values[n // 2]
            return round(mean, 2), round(median, 2), round(values[0], 2), round(values[-1], 2)

        if num_senders > 0 and total_confirmed > 0 and all_delays:
            latency_stats = compute_stats(all_delays)
            pdr_stats = compute_stats(pdr_list)
            throughput_stats = compute_stats(throughput_list)

            writer.writerow({
                "File": filename,
                "Latency Mean (ms)": latency_stats[0],
                "Latency Median (ms)": latency_stats[1],
                "Latency Min (ms)": latency_stats[2],
                "Latency Max (ms)": latency_stats[3],
                "Throughput % Mean": pdr_stats[0],
                "Throughput % Median": pdr_stats[1],
                "Throughput % Min": pdr_stats[2],
                "Throughput % Max": pdr_stats[3],
                "Sendrate Mean (Bps)": throughput_stats[0],
                "Sendrate Median (Bps)": throughput_stats[1],
                "Sendrate Min (Bps)": throughput_stats[2],
                "Sendrate Max (Bps)": throughput_stats[3],
                "Sent": total_sent // num_senders,
                "Confirmed": total_confirmed // num_senders,
                "Received": total_received // num_senders
            })

print(f"\n✅ Per-file statistics (mean, median, min, max) written to: {output_csv}")
