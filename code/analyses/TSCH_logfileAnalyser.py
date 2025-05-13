import re
from collections import defaultdict
import os
import argparse
import csv
from datetime import datetime

# === Argument parsing ===
parser = argparse.ArgumentParser(description="Parse COOJA TSCH log and generate stats.")
parser.add_argument("input_path", help="Path to the COOJA log file")
args = parser.parse_args()
input_path = args.input_path
trimmed_output = False

# === Data structures ===
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
last_association_time = 0
last_timestamp = 0

# === Extra counters ===
queue_full_counts = defaultdict(int)
tsch_send_counts = defaultdict(int)
first_send_done_time = {}
sender_nodes = [str(n) for n in [10, 11, 19, 2, 20, 21, 22, 23, 24, 25, 26, 27, 28, 3, 4, 5, 6, 7, 8, 9]]

# === Read full file first ===
with open(input_path, 'r') as file:
    lines = list(file)

# === Process each line ===
for i, line in enumerate(lines):
    matchTimestamp = re.match(r'^(\d+)', line)
    if matchTimestamp:
        timestamp = int(matchTimestamp.group(1))
        last_timestamp = max(last_timestamp, timestamp)

    # Count lines per node
    node_match = re.match(r'^\d+\s+(\d+)\s+\[.*?\]', line)
    if node_match:
        node = node_match.group(1)
        if node in sender_nodes:
            line_counts[node] += 1

    # Count TSCH sends
    tsch_match = re.match(r'^\d+\s+(\d+)\s+\[INFO: TSCH\s+\] send packet to .*', line)
    if tsch_match:
        node = tsch_match.group(1)
        if node in sender_nodes:
            tsch_send_counts[node] += 1

    # Detect 'Sending message' lines
    send_match = re.match(r'^(\d+)\s+(\d+)\s+Sending message: \'(.+)\' to fd00::210:10:10:10', line)
    if send_match:
        time = int(send_match.group(1))
        sender_node = send_match.group(2)
        message = send_match.group(3).strip()
        if sender_node in sender_nodes:
            sent_counts[sender_node] += 1
            sent_messages[message] = (time, sender_node)
            first_send_time[sender_node] = min(first_send_time[sender_node], time)

            # Check next 10 lines for confirmation
            for followup_line in lines[i+1:i+11]:
                tsch_confirm = re.match(r'^\d+\s+' + sender_node + r'\s+\[INFO: TSCH\s+\] send packet to .*', followup_line)
                if tsch_confirm:
                    confirmed_sent_counts[sender_node] += 1
                    break

    # Detect received messages
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

    # Detect queue full
    queue_match = re.match(r'^\d+\s+(\d+)\s+\[.*?\] ! can\'t send packet .* queue \d+/\d+ \d+/\d+', line)
    if queue_match:
        node = queue_match.group(1)
        if node in sender_nodes:
            queue_full_counts[node] += 1

    # Detect end marker per node
    send_done_match = re.match(r'^(\d+)\s+(\d+)\s+All messages send:', line)
    if send_done_match:
        time = int(send_done_match.group(1))
        node = send_done_match.group(2)
        if node in sender_nodes and node not in first_send_done_time:
            first_send_done_time[node] = time
        last_association_time = max(last_association_time, time)

# === Summary Output ===
print("\nSender Node | Avg Delay (ms) | Sent | Confirmed | Received | Success % | Throughput (Bps) | Avg Hops | Lines | Queue Full | TSCH Sends")
print("------------|----------------|------|-----------|----------|-----------|------------------|----------|--------|-------------|-------------")

total_sent = total_confirmed = total_received = total_delay = total_avg_hops = total_throughput = 0
num_senders = 0

for sender in sorted(sender_nodes):
    sent = sent_counts[sender]
    confirmed = confirmed_sent_counts[sender]
    received = recv_counts[sender]
    ratio = (received / confirmed * 100) if confirmed > 0 else 0
    avg_delay = sum(sender_delays[sender]) / received if received > 0 else 0
    avg_hops = sum(sender_hops[sender]) / received if received > 0 else 0
    time_span = (last_recv_time[sender] - first_send_time[sender]) / 1000
    throughput = (recv_bytes[sender] / (time_span / 1000)) if time_span > 0 else 0

    print(f"{sender:11} | {avg_delay:14.2f} | {sent:4} | {confirmed:9} | {received:8} | {ratio:9.1f}% | {throughput:16.2f} | {avg_hops:.2f} | {line_counts[sender]:6} | {queue_full_counts[sender]:11} | {tsch_send_counts[sender]:11}")

    if received > 0:
        total_sent += sent
        total_confirmed += confirmed
        total_received += received
        total_delay += avg_delay
        total_avg_hops += avg_hops
        total_throughput += throughput
        num_senders += 1

print("-" * 132)
if num_senders > 0:
    print(f"{'MEAN':11} | {total_delay/num_senders:14.2f} | "
          f"{total_sent//num_senders:4} | {total_confirmed//num_senders:9} | {total_received//num_senders:8} | "
          f"{(total_received/total_confirmed*100):9.1f}% | {total_throughput/num_senders:16.2f} | "
          f"{total_avg_hops/num_senders:.2f} | {'-'*6} | {'-'*11} | {'-'*11}")


'''


# === CSV Export ===
csv_path = os.path.splitext(input_path)[0] + ".csv"
timestampbatch = datetime.now().strftime('%Y%m%d%H%M%S')

with open(csv_path, 'a', newline='') as csvfile:
    writer = csv.writer(csvfile)
    writer.writerow(["Timestamp", "Logfile", "Sender Node", "Avg Delay (ms)", "Sent", "Confirmed Sent",
                     "Received", "Success %", "Throughput (Bps)", "Avg Hops", "Lines", "Queue Full", "TSCH Sends"])
    for sender in sorted(sender_nodes):
        sent = sent_counts[sender]
        confirmed = confirmed_sent_counts[sender]
        received = recv_counts[sender]
        ratio = (received / confirmed * 100) if confirmed > 0 else 0
        avg_delay = sum(sender_delays[sender]) / received if received > 0 else 0
        avg_hops = sum(sender_hops[sender]) / received if received > 0 else 0
        time_span = (last_recv_time[sender] - first_send_time[sender]) / 1000
        throughput = (recv_bytes[sender] / (time_span / 1000)) if time_span > 0 else 0

        writer.writerow([
            timestampbatch,
            os.path.basename(input_path),
            sender,
            round(avg_delay, 2),
            sent,
            confirmed,
            received,
            round(ratio, 1),
            round(throughput, 2),
            round(avg_hops, 2),
            line_counts[sender],
            queue_full_counts[sender],
            tsch_send_counts[sender]
        ])

print(f"\n✅ CSV saved to: {csv_path}")
'''