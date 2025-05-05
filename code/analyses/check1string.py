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

with open('code/analyses/COOJA.testlog', 'r') as file:
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
        recv_match = re.match(r'^(\d+)\s+16\s+Data received from .*?:\s+\'.+\'', line)
        if recv_match:
            time = int(recv_match.group(1))
            message_match = re.search(r': \'(.+)\'$', line.strip())
            if message_match:
                message = message_match.group(1).strip()
                if message in sent_messages:
                    send_time, sender_node = sent_messages[message]
                    delay = time - send_time

                    sender_delays[sender_node].append(delay)
                    recv_counts[sender_node] += 1
                    recv_bytes[sender_node] += len(message)
                    last_recv_time[sender_node] = max(last_recv_time[sender_node], time)

# Resultaatoverzicht
print("\nSender Node | Avg Delay (ms) | Sent | Received | Success % | Throughput (Bps)")
print("------------|----------------|------|----------|-----------|------------------")
all_senders = sorted(set(sent_counts.keys()) | set(recv_counts.keys()))
for sender in all_senders:
    sent = sent_counts[sender]
    received = recv_counts.get(sender, 0)
    ratio = (received / sent) * 100 if sent > 0 else 0
    avg_delay = sum(sender_delays[sender]) / received if received > 0 else 0

    time_span = (last_recv_time[sender] - first_send_time[sender]) / 1000  # ms → sec
    throughput = (recv_bytes[sender] / time_span) if time_span > 0 else 0

    print(f"{sender:11} | {avg_delay:14.2f} | {sent:4} | {received:8} | {ratio:9.1f}% | {throughput:16.2f}")
