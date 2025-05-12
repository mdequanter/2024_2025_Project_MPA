import re

logfile = "code/analyses/logfiles/TSCH_80_1.testlog"  # ← replace with your actual filename
send_times = []

node = 6  # Node ID to analyze

with open(logfile, 'r') as file:
    for line in file:
        match = re.match(fr'^(\d+)\s+{node}\s+Sending message: \'(.+?)\' to .*', line)
        if match:
            tick = int(match.group(1))
            message = match.group(2)
            time_in_seconds = tick / 1_000_000
            send_times.append((time_in_seconds, message))

# Calculate and print intervals
print("Node 10 sending messages and time between them:\n")

previous_time = None
for time, message in send_times:
    if previous_time is not None:
        delta = time - previous_time
        print(f"{time:.2f}s - '{message}' (delta {delta:.2f}s)")
    else:
        print(f"{time:.2f}s - '{message}' (first message)")
    previous_time = time


print (f"Number of messages send by node {node}: {len(send_times)}")