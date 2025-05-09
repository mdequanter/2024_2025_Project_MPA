import re
from collections import defaultdict

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
last_association_time = 0
associated_nodes = {}


with open('code/analyses/logfiles/TSCH_1_1.testlog', 'r') as file:
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

            if message in sent_messages:
                send_time, sender_node = sent_messages[message]
                delay = time - send_time

                sender_delays[sender_node].append(delay)
                sender_hops[sender_node].append(hops)
                recv_counts[sender_node] += 1
                recv_bytes[sender_node] += len(message)
                last_recv_time[sender_node] = max(last_recv_time[sender_node], time)

        match = re.match(r'^(\d+)\s+(\d+)\s+\[.*?\] Associated with', line)
        if match:
            time = int(match.group(1))
            node = int(match.group(2))
            print(time)

            associated_nodes[node] = time
            if time > last_association_time:
                last_association_time = time

print(f"Laatste TSCH associatie: {last_association_time} ticks")

print("\nSender Node | Avg Delay (s)  | Sent | Received | Success % | Throughput (Bps) | Avg Hops")
print("------------|----------------|------|----------|-----------|------------------|----------")

# Totals for calculating means
total_delay = 0
total_sent = 0
total_received = 0
total_success = 0
total_throughput = 0
total_avg_hops = 0
num_senders = 0

all_senders = sorted(set(sent_counts.keys()) | set(recv_counts.keys()))
for sender in all_senders:
    sent = sent_counts[sender]
    received = recv_counts.get(sender, 0)
    ratio = (received / sent) * 100 if sent > 0 else 0
    avg_delay = sum(sender_delays[sender]) / received if received > 0 else 0
    avg_hops = sum(sender_hops[sender]) / received if received > 0 else 0

    time_span = (last_recv_time[sender] - first_send_time[sender]) / 1000  # ms → sec
    throughput = (recv_bytes[sender] / (time_span / 1000)) if time_span > 0 else 0

    print(f"{sender:11} | {avg_delay/1000:14.2f} | {sent:4} | {received:8} | {ratio:9.1f}% | {throughput:16.2f} | {avg_hops:.2f}")

    if received > 0:
        total_delay += avg_delay / 1000
        total_avg_hops += avg_hops
    total_sent += sent
    total_received += received
    total_success += ratio
    total_throughput += throughput
    num_senders += 1

print("-" * 85)
print(f"{'MEAN':11} | {total_delay/num_senders:14.2f} | "
      f"{total_sent//num_senders:4} | {total_received//num_senders:8} | "
      f"{total_success/num_senders:9.1f}% | {total_throughput/num_senders:16.2f} | "
      f"{total_avg_hops/num_senders:.2f}")
