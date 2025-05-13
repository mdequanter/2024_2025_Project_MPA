import re
from collections import defaultdict
import argparse

# Define expected nodes (e.g. node IDs from 1 to 20)
expected_nodes = [str(n) for n in range(1, 21)]
root_node = '1'  # root does not need a parent

# Track status per node
has_rank = defaultdict(bool)
has_parent = defaultdict(bool)
first_tick_seen = defaultdict(lambda: float('inf'))

# Tick when the full network is considered built
network_built_tick = None

# === Configuration ===
parser = argparse.ArgumentParser(description="Parse COOJA test log.")
parser.add_argument("input_path", help="Path to the COOJA log file")
args = parser.parse_args()

logfile = args.input_path

# === Log parsing ===
with open(logfile) as file:
    for line in file:
        # Extract timestamp at the start of the line
        timestamp_match = re.match(r'^(\d+)', line)
        tick = int(timestamp_match.group(1)) if timestamp_match else None

        # Detect RPL rank (node is part of DODAG)
        match_rank = re.match(r'^\d+\s+(\d+)\s+\[DBG : RPL\s+\] RPL: MOP \d+ OCP \d+ rank (\d+)', line)
        if match_rank:
            node = match_rank.group(1)
            if node in expected_nodes:
                has_rank[node] = True
                first_tick_seen[node] = min(first_tick_seen[node], tick)

        # Detect preferred parent (for non-root nodes)
        match_parent = re.match(r'^\d+\s+(\d+)\s+\[DBG : RPL\s+\] RPL: nbr .*--\s+1', line)
        if match_parent:
            node = match_parent.group(1)
            if node in expected_nodes:
                has_parent[node] = True
                first_tick_seen[node] = min(first_tick_seen[node], tick)

        # Check if full network is built
        all_ready = True
        for n in expected_nodes:
            if n == root_node:
                if not has_rank[n]:
                    all_ready = False
                    break
            else:
                if not (has_rank[n] and has_parent[n]):
                    all_ready = False
                    break

        if all_ready and network_built_tick is None:
            network_built_tick = tick

# === Output per node ===
print("Network status per node:")
for node in sorted(expected_nodes, key=int):
    tick_value = first_tick_seen[node]
    second_value = tick_value / 1_000_000 if tick_value < float('inf') else 'n/a'
    print(f"Node {node}: rank={'✓' if has_rank[node] else '✗'} | parent={'-' if node == root_node else ('✓' if has_parent[node] else '✗')} | first seen at second {second_value}")

# === Final result ===
if network_built_tick:
    built_sec = network_built_tick / 1_000_000
    print(f"\n✅ Network fully built at second: {built_sec:.2f}")
else:
    print("\n❌ Network was not fully built in the log file.")
