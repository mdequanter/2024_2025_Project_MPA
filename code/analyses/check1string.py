import re
from collections import defaultdict
import os

# Verzonden berichten: message => (timestamp, sender_node)
sent_messages = {}

# Verzameldata per sender
sender_delays = defaultdict(list)
sent_counts = defaultdict(int)
recv_counts = defaultdict(int)
recv_bytes = defaultdict(int)
first_send_time = defaultdict(lambda: float('inf'))
last_recv_time = defaultdict(lambda: 0)
sender_hops = defaultdict(list)
associated_nodes = {}
line_counts = defaultdict(int)
last_association_time = 0
last_timestamp = 0

# Extra counters
queue_full_counts = defaultdict(int)
tsch_send_counts = defaultdict(int)

input_path = 'code/analyses/logfiles/TSCH_1_4.testlog'
trimmed_output = False

# Tijdstip waarop elke sender node "All messages send" heeft gelogd
first_send_done_time = {}

# Enkel deze nodes analyseren
sender_nodes = [10, 11, 19, 2, 20, 21, 22, 23, 24, 25, 26, 27, 28, 3, 4, 5, 6, 7, 8, 9]
sender_nodes = [str(n) for n in sender_nodes]

with open(input_path, 'r') as file:
    for line in file:
        # Tel lijnen per node
        line_node_match = re.match(r'^\d+\s+(\d+)\s+\[.*?\]', line)
        if line_node_match:
            node = line_node_match.group(1)
            if node in sender_nodes:
                line_counts[node] += 1

        # TSCH send line (additional counter)
        tsch_send_match = re.match(r'^\d+\s+(\d+)\s+\[INFO: TSCH\s+\] send packet to .*', line)
        if tsch_send_match:
            node = tsch_send_match.group(1)
            if node in sender_nodes:
                tsch_send_counts[node] += 1

        # Verstuurd bericht detecteren
        send_match = re.match(r'^(\d+)\s+(\d+)\s+Sending message: \'(.+)\' to fd00::210:10:10:10', line)
        if send_match:
            time = int(send_match.group(1))
            sender_node = send_match.group(2)
            message = send_match.group(3).strip()
            if sender_node in sender_nodes:
                sent_messages[message] = (time, sender_node)
                sent_counts[sender_node] += 1
                first_send_time[sender_node] = min(first_send_time[sender_node], time)

        # Ontvangen bericht detecteren
        recv_match = re.match(
            r'^(\d+)\s+16\s+Data received from .*? in (\d+) hops with datalength \d+: \'(.+)\'', line)
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

        # All messages send
        send_done_match = re.match(r'^(\d+)\s+(\d+)\s+All messages send:', line)
        if send_done_match:
            time = int(send_done_match.group(1))
            node = send_done_match.group(2)
            if node in sender_nodes and node not in first_send_done_time:
                first_send_done_time[node] = time
            last_association_time = max(last_association_time, time)

        # Laatste timestamp
        matchTimestamp = re.match(r'^(\d+)\s+', line)
        if matchTimestamp:
            timestamp = int(matchTimestamp.group(1))
            last_timestamp = max(last_timestamp, timestamp)

        # Queue full errors
        queue_match = re.match(r'^\d+\s+(\d+)\s+\[.*?\] ! can\'t send packet .* queue \d+/\d+ \d+/\d+', line)
        if queue_match:
            node = queue_match.group(1)
            if node in sender_nodes:
                queue_full_counts[node] += 1

print("\n'queue full' ERRORS per node:")
for node in sorted(queue_full_counts.keys(), key=int):
    print(f"Node {node}: {queue_full_counts[node]} times")

if len(first_send_done_time) < len(sender_nodes):
    missing = set(sender_nodes) - set(first_send_done_time.keys())
    print(f"\n⚠️ No 'All messages send' for: {sorted(missing)}")
else:
    print("\n✅ All sender nodes have a 'All messages send:' line.")

last_node = max(first_send_done_time, key=first_send_done_time.get)
last_time = first_send_done_time[last_node]
print(f"\nLast 'All messages send:' line: Node {last_node} on {last_time} ticks")
print(f"Last line in file: {last_timestamp} ticks")

if trimmed_output:
    trimTempFile = input_path + ".tmp"
    with open(input_path, 'r') as infile, open(trimTempFile, 'w') as outfile:
        for line in infile:
            match = re.match(r'^(\d+)\s+', line)
            if match:
                timestamp = int(match.group(1))
                if timestamp <= last_time:
                    outfile.write(line)
            else:
                outfile.write(line)
    os.remove(input_path)
    os.rename(trimTempFile, input_path)

print("\nSender Node | Avg Delay (s)  | Sent | Received | Success % | Throughput (Bps) | Avg Hops | Lines | Queue Full | TSCH Sends")
print("------------|----------------|------|----------|-----------|------------------|----------|--------|-------------|-------------")

total_delay = 0
total_sent = 0
total_received = 0
total_success = 0
total_throughput = 0
total_avg_hops = 0
num_senders = 0

all_senders = sorted(sender_nodes)
for sender in all_senders:
    sent = sent_counts[sender]
    received = recv_counts.get(sender, 0)
    ratio = (received / sent) * 100 if sent > 0 else 0
    avg_delay = sum(sender_delays[sender]) / received if received > 0 else 0
    avg_hops = sum(sender_hops[sender]) / received if received > 0 else 0
    time_span = (last_recv_time[sender] - first_send_time[sender]) / 1000  # ms → sec
    throughput = (recv_bytes[sender] / (time_span / 1000)) if time_span > 0 else 0
    queue_errors = queue_full_counts[sender]
    tsch_sends = tsch_send_counts[sender]

    print(f"{sender:11} | {avg_delay/1000:14.2f} | {sent:4} | {received:8} | {ratio:9.1f}% | {throughput:16.2f} | {avg_hops:.2f} | {line_counts[sender]:6} | {queue_errors:11} | {tsch_sends:11}")

    if received > 0:
        total_delay += avg_delay / 1000
        total_avg_hops += avg_hops
    total_sent += sent
    total_received += received
    total_success += ratio
    total_throughput += throughput
    num_senders += 1

print("-" * 132)
print(f"{'MEAN':11} | {total_delay/num_senders:14.2f} | "
      f"{total_sent//num_senders:4} | {total_received//num_senders:8} | "
      f"{total_success/num_senders:9.1f}% | {total_throughput/num_senders:16.2f} | "
      f"{total_avg_hops/num_senders:.2f} | {'-'*6} | {'-'*11} | {'-'*11}")

import csv
from datetime import datetime

# Bepaal CSV-bestandspad
csv_path = os.path.splitext(input_path)[0] + '.csv'

timestampbatch = datetime.now().strftime('%Y%m%d%H%M%S')

with open(csv_path, 'w', newline='') as csvfile:
    writer = csv.writer(csvfile)
    writer.writerow(["Timestamp","logfile","Sender Node", "Avg Delay (ms)", "Sent", "Received", "Success %", "Throughput (Bps)", "Avg Hops", "Lines", "Queue Full", "TSCH Sends"])

    for sender in all_senders:
        sent = sent_counts[sender]
        received = recv_counts.get(sender, 0)
        ratio = (received / sent) * 100 if sent > 0 else 0
        avg_delay = sum(sender_delays[sender]) / received if received > 0 else 0
        avg_hops = sum(sender_hops[sender]) / received if received > 0 else 0
        time_span = (last_recv_time[sender] - first_send_time[sender]) / 1000  # ms → sec
        throughput = (recv_bytes[sender] / (time_span / 1000)) if time_span > 0 else 0
        queue_errors = queue_full_counts[sender]
        tsch_sends = tsch_send_counts[sender]

        writer.writerow([
            timestampbatch,
            os.path.basename(input_path),
            sender,
            round(avg_delay / 1000, 2),
            sent,
            received,
            round(ratio, 1),
            round(throughput, 2),
            round(avg_hops, 2),
            line_counts[sender],
            queue_errors,
            tsch_sends
        ])

print(f"\n✅ CSV weggeschreven naar: {csv_path}")
