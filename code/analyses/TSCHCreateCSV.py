import os
import re
import csv
from collections import defaultdict

# === Configuration ===
log_dir = "code/analyses/logfiles"
output_csv = "code/analyses/tsch_summary_means.csv"
sender_nodes = [str(n) for n in [10, 11, 19, 2, 20, 21, 22, 23, 24, 25, 26, 27, 28, 3, 4, 5, 6, 7, 8, 9]]

# === Prepare CSV output ===
with open(output_csv, mode='w', newline='') as csvfile:
    fieldnames = [
        "File", "End-to-End latency(ms)", "Sent",
        "Confirmed", "Received", "Throughput %", "Sendrate (Bps)"
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
        total_sent = total_confirmed = total_received = total_delay = total_throughput = 0
        num_senders = 0

        for sender in sender_nodes:
            sent = sent_counts[sender]
            confirmed = confirmed_sent_counts[sender]
            received = recv_counts[sender]

            if confirmed > 0 and received > 0:
                avg_delay = sum(sender_delays[sender]) / (received * 1000)
                time_span = (last_recv_time[sender] - first_send_time[sender]) / 1000
                throughput = (recv_bytes[sender] / (time_span / 1000)) if time_span > 0 else 0

                total_sent += sent
                total_confirmed += confirmed
                total_received += received
                total_delay += avg_delay
                total_throughput += throughput
                num_senders += 1

        if num_senders > 0 and total_confirmed > 0:
            writer.writerow({
                "File": filename,
                "End-to-End latency(ms)": round(total_delay / num_senders, 2),
                "Sent": total_sent // num_senders,
                "Confirmed": total_confirmed // num_senders,
                "Received": total_received // num_senders,
                "Throughput %": round((total_received / total_confirmed) * 100, 2),
                "Sendrate (Bps)": round(total_throughput / num_senders, 2)
            })

print(f"\n✅ Per-file MEAN summary written to: {output_csv}")
