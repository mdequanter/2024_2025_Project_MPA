import re
from collections import defaultdict
import os
import csv
from datetime import datetime
import glob

# === Parameters ===
timing_prefix = "TSCH_75"
log_dir = "code/analyses/logfiles"
pattern = os.path.join(log_dir, f"{timing_prefix}_*.testlog")
log_files = sorted(glob.glob(pattern))

# Ensure output directory exists
os.makedirs(log_dir, exist_ok=True)

# === Output CSV Path ===
output_csv = os.path.join(log_dir, f"{timing_prefix}_combined.csv")
timestampbatch = datetime.now().strftime('%Y%m%d%H%M%S')

# === Data for all logs ===
combined_rows = []

# === Fixed sender nodes ===
sender_nodes = [str(n) for n in [10, 11, 19, 2, 20, 21, 22, 23, 24, 25, 26, 27, 28, 3, 4, 5, 6, 7, 8, 9]]

# === Process each file ===
for input_path in log_files:
    sent_messages = {}
    sender_delays = defaultdict(list)
    sent_counts = defaultdict(int)
    confirmed_sent_counts = defaultdict(int)
    recv_counts = defaultdict(int)
    recv_bytes = defaultdict(int)
    first_send_time = defaultdict(lambda: float('inf'))
    last_recv_time = defaultdict(lambda: 0)
    sender_hops = defaultdict(list)
    line_counts = defaultdict(int)
    queue_full_counts = defaultdict(int)
    tsch_send_counts = defaultdict(int)

    with open(input_path, 'r') as file:
        lines = list(file)

    for i, line in enumerate(lines):
        if re.match(r'^(\d+)', line):
            node_match = re.match(r'^\d+\s+(\d+)\s+\[.*?\]', line)
            if node_match:
                node = node_match.group(1)
                if node in sender_nodes:
                    line_counts[node] += 1

            tsch_match = re.match(r'^\d+\s+(\d+)\s+\[INFO: TSCH\s+\] send packet to .*', line)
            if tsch_match:
                node = tsch_match.group(1)
                if node in sender_nodes:
                    tsch_send_counts[node] += 1

            send_match = re.match(r'^(\d+)\s+(\d+)\s+Sending message: \'(.+)\' to fd00::210:10:10:10', line)
            if send_match:
                time = int(send_match.group(1))
                sender_node = send_match.group(2)
                message = send_match.group(3).strip()
                if sender_node in sender_nodes:
                    sent_counts[sender_node] += 1
                    sent_messages[message] = (time, sender_node)
                    first_send_time[sender_node] = min(first_send_time[sender_node], time)

                    for followup_line in lines[i+1:i+11]:
                        tsch_confirm = re.match(r'^\d+\s+' + sender_node + r'\s+\[INFO: TSCH\s+\] send packet to .*', followup_line)
                        if tsch_confirm:
                            confirmed_sent_counts[sender_node] += 1
                            break

            recv_match = re.match(r'^(\d+)\s+16\s+Data received from .*? in (\d+) hops with datalength \d+: \'(.+)\'', line)
            if recv_match:
                time = int(recv_match.group(1))
                hops = int(recv_match.group(2))
                message = recv_match.group(3).strip()
                if message in sent_messages:
                    send_time, sender_node = sent_messages[message]
                    if sender_node in sender_nodes:
                        delay = time - send_time
                        sender_delays[sender_node].append(delay)
                        sender_hops[sender_node].append(hops)
                        recv_counts[sender_node] += 1
                        recv_bytes[sender_node] += len(message)
                        last_recv_time[sender_node] = max(last_recv_time[sender_node], time)

            queue_match = re.match(r'^\d+\s+(\d+)\s+\[.*?\] ! can\'t send packet .* queue \d+/\d+ \d+/\d+', line)
            if queue_match:
                node = queue_match.group(1)
                if node in sender_nodes:
                    queue_full_counts[node] += 1

    for sender in sorted(sender_nodes):
        sent = sent_counts[sender]
        confirmed = confirmed_sent_counts[sender]
        received = recv_counts[sender]
        ratio = (received / confirmed * 100) if confirmed > 0 else 0
        avg_delay = sum(sender_delays[sender]) / received if received > 0 else 0
        avg_hops = sum(sender_hops[sender]) / received if received > 0 else 0
        time_span = (last_recv_time[sender] - first_send_time[sender]) / 1000
        throughput = (recv_bytes[sender] / (time_span / 1000)) if time_span > 0 else 0

        combined_rows.append([
            timestampbatch,
            os.path.basename(input_path),
            sender,
            round(avg_delay, 2),
            sent,
            confirmed,
            received,
            round(ratio, 1),
            round(throughput, 2),
            round(avg_hops, 2)
            #line_counts[sender],
            #queue_full_counts[sender],
            #tsch_send_counts[sender]
        ])

# === Write final CSV ===
with open(output_csv, 'w', newline='') as csvfile:
    writer = csv.writer(csvfile)
    writer.writerow(["Timestamp", "Logfile", "Sender Node", "Avg Delay (ms)", "Sent", "Confirmed Sent",
                     "Received", "Success %", "Throughput (Bps)", "Avg Hops"])
    writer.writerows(combined_rows)

output_csv
