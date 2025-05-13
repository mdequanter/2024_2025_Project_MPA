import re
from collections import defaultdict

import argparse

# === CLI Argument Configuration ===
parser = argparse.ArgumentParser(description="Parse COOJA log and plot per-second metrics with latency.")
parser.add_argument("input_path", help="Path to the COOJA log file")
args = parser.parse_args()

logfile = args.input_path
csv_output = logfile.replace('.testlog', '_stats.csv')

saveLogs = True


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

# Extra: "not for us" warnings per node
not_for_us_counts = defaultdict(int)

with open(logfile, 'r') as file:
    for line in file:
        # Verstuurd bericht detecteren
        send_match = re.match(r'^(\d+)\s+(\d+)\s+Sending message: \'(.+)\' to fd00::210:10:10:10', line)
        if send_match:
            time = int(send_match.group(1))
            sender_node = send_match.group(2)
            message = send_match.group(3).strip()

            sent_messages[message] = (time, sender_node)
            sent_counts[sender_node] += 1
            first_send_time[sender_node] = min(first_send_time[sender_node], time)

        # Ontvangen bericht detecteren op node 16
        recv_match = re.match(
            r'^(\d+)\s+16\s+Data received from .*? in (\d+) hops with datalength \d+: \'(.+)\'', line)
        if recv_match:
            time = int(recv_match.group(1))
            hops = int(recv_match.group(2))
            message = recv_match.group(3).strip()

            #print(f"Received message: {message} | Hops: {hops}")

            if message in sent_messages:
                send_time, sender_node = sent_messages[message]
                delay = time - send_time

                sender_delays[sender_node].append(delay)
                sender_hops[sender_node].append(hops)
                recv_counts[sender_node] += 1
                recv_bytes[sender_node] += len(message)
                last_recv_time[sender_node] = max(last_recv_time[sender_node], time)

        # Detecteer "not for us" waarschuwingen
        not_for_us_match = re.match(r'^\d+\s+(\d+)\s+\[WARN: CSMA\s+\]\s+not for us', line)
        if not_for_us_match:
            node = not_for_us_match.group(1)
            not_for_us_counts[node] += 1
'''
#why not for us? All nodes on a wireless channel receive all packets, but they must filter out packets that aren’t meant for them.
This log entry indicates that the MAC layer did its job of filtering.
A high frequency of "not for us" logs indicates:
Many unicast transmissions in the area
The node is in range of many senders, but not the target of their messages
So this may overload this node's radio or queue (todo need to check input queue or input, maybe 2 ), and slow it down, so we see less packets received for this senders node
'''

print("\nSender Node | End-to-End latency(ms)  | Sent | Received | Throughput % | sendrate(Bps) | Not-for-us | Avg Hops")
print("------------|----------------|------|----------|-----------|------------------|-------------|----------")

# Totals for calculating means
total_delay = 0
total_sent = 0
total_received = 0
total_success = 0
total_throughput = 0
total_not_for_us = 0
total_avg_hops = 0
num_senders = 0

import csv
import os

from datetime import datetime 


timestampbatch = datetime.now().strftime('%Y%m%d%H%M%S')

sender_nodes = [str(n) for n in [10, 11, 19, 2, 20, 21, 22, 23, 24, 25, 26, 27, 28, 3, 4, 5, 6, 7, 8, 9]]

# Ensure output directory exists
os.makedirs(os.path.dirname(csv_output), exist_ok=True)

# Prepare to write to CSV
write_header = not os.path.exists(csv_output)  # Only write header if file doesn't exist

with open(csv_output, mode='a', newline='') as csvfile:
    fieldnames = [
        'batch','timestamp','logfile', 'sendrate', 'sender', 'avg_delay_s', 'sent', 'received',
        'success_ratio_percent', 'throughput_bytes_per_s', 'not_for_us', 'avg_hops'
    ]
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    if write_header:
        writer.writeheader()

    all_senders = sorted(set(sent_counts.keys()) and set(recv_counts.keys()) and set(not_for_us_counts.keys()))
    for sender in all_senders:
        sent = sent_counts[sender]
        if sent > 0:
            received = recv_counts.get(sender, 0)
            ratio = (received / sent) * 100 if sent > 0 else 0
            avg_delay = sum(sender_delays[sender]) / received if received > 0 else 0
            avg_hops = sum(sender_hops[sender]) / received if received > 0 else 0
            time_span = (last_recv_time[sender] - first_send_time[sender]) / 1000  # ms → sec
            throughput = (recv_bytes[sender] / (time_span / 1000)) if time_span > 0 else 0
            not_for_us = not_for_us_counts.get(sender, 0)

            print(f"{sender:11} | {avg_delay/1000:14.2f} | {sent:4} | {received:8} | {ratio:9.1f}% | {throughput:16.2f} | {not_for_us:11} | {avg_hops:.2f}")

            writer.writerow({
                'timestamp':timestampbatch,
                'logfile': os.path.basename(logfile),
                'sender': sender,
                'avg_delay_s': round(avg_delay / 1000, 3),
                'sent': sent,
                'received': received,
                'success_ratio_percent': round(ratio, 2),
                'throughput_bytes_per_s': round(throughput, 2),
                'not_for_us': not_for_us,
                'avg_hops': round(avg_hops, 2)
            })

            # Accumulate totals
            if received > 0:
                total_delay += avg_delay / 1000
                total_avg_hops += avg_hops
            total_sent += sent
            total_received += received
            total_success += ratio
            total_throughput += throughput
            total_not_for_us += not_for_us
            num_senders += 1

# Print mean line
print("-" * 96)
print(f"{'MEAN':11} | {total_delay/num_senders:14.2f} | "
    f"{total_sent//num_senders:4} | {total_received//num_senders:8} | "
    f"{total_success/num_senders:9.1f}% | {total_throughput/num_senders:16.2f} | "
    f"{total_not_for_us//num_senders:11} | {total_avg_hops/num_senders:.2f}")