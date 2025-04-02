#!/usr/bin/env python3

# Result shows :


# Node ID Packets Sent    Packets Received        PDR (%) Avg Delay (ms)
# ------- ------------    --------------- ------- ------------
# 1       100     0       0.00%   0.00 ms
# 2       0       100     0.00%   23606.00 ms
# 3       0       100     0.00%   23606.00 ms
# 4       0       100     0.00%   234734.00 ms
# 5       0       100     0.00%   234734.00 ms
# 6       0       100     0.00%   23606.00 ms
# 7       0       100     0.00%   23606.00 ms
# 8       0       100     0.00%   23606.00 ms
# 9       0       100     0.00%   234734.00 ms

# In this case, the PDR is 0% for all nodes, which means that no packets were successfully received by the destination nodes.
# The average delay is the average time taken for a packet to be received by the destination nodes after being sent by the source node.
# In this case, the average delay is quite high for all nodes, ranging from 0 ms to 234734 ms. This indicates that there were significant delays in packet delivery in the network.
# This is the case for node 4, 5 and 9.  They are further away from the source node, which results in higher delays due to the multi-hop nature of the network.


import os
import sys
import matplotlib.pyplot as plt
import pandas as pd
from collections import defaultdict

# Class to store node statistics
class NodeStats:
    def __init__(self, node_id):
        self.node_id = node_id
        self.packets_sent = 0
        self.packets_received = 0
        self.send_times = []
        self.receive_times = []
        self.delays = []

# Function to process log file and extract relevant data
def analyze_log(filename):
    nodes = defaultdict(lambda: NodeStats(0))
    send_time = None
    
    with open(filename, "r") as file:
        for line in file:
            fields = line.strip().split()
            try:
                timestamp = int(fields[0])  # first column is timestamp
                node_id = int(fields[1])  # second column is node ID
            except:
                continue
            if node_id not in nodes:
                nodes[node_id] = NodeStats(node_id)

            # Detect sent packets
            if "Send to:" in line:
                nodes[node_id].packets_sent += 1
                send_time = timestamp  # Store send timestamp
                nodes[node_id].send_times.append(send_time)

            # Detect received packets
            if "In:" in line:
                nodes[node_id].packets_received += 1
                nodes[node_id].receive_times.append(timestamp)
                if send_time is not None:
                    delay = timestamp - send_time
                    nodes[node_id].delays.append(delay)
    return nodes

# Function to compute and plot PDR and delay
def plot_results(nodes):
    ids = list(sorted(nodes.keys()))
    sent_packets = [nodes[n].packets_sent for n in ids]
    received_packets = [nodes[n].packets_received for n in ids]
    
    # Compute Packet Delivery Ratio (PDR)
    pdr_values = [(nodes[n].packets_received / nodes[n].packets_sent * 100) if nodes[n].packets_sent > 0 else 0 for n in ids]
    
    # Compute average delay per node
    avg_delays = [sum(nodes[n].delays)/len(nodes[n].delays) if nodes[n].delays else 0 for n in ids]
    
    # Display results
    print("Node ID\tPackets Sent\tPackets Received\tPDR (%)\tAvg Delay (ms)")
    print("-------\t------------\t---------------\t-------\t------------")
    for n in ids:
        print(f"{n}\t{nodes[n].packets_sent}\t{nodes[n].packets_received}\t{pdr_values[ids.index(n)]:.2f}%\t{avg_delays[ids.index(n)]:.2f} ms")
    
    # Create DataFrame for visualization
    df_pdr = pd.DataFrame({"PDR (%)": pdr_values}, index=ids)
    df_pdr.plot(kind="bar", color='blue', legend=False)
    plt.xlabel("Node ID")
    plt.ylabel("Packet Delivery Ratio (%)")
    plt.title("PDR per Node")
    plt.ylim(0, 100)
    plt.savefig("plot_PDR.pdf", format="pdf", bbox_inches="tight")
    plt.close()
    
    df_delay = pd.DataFrame({"Avg Delay (ms)": avg_delays}, index=ids)
    df_delay.plot(kind="bar", color='red', legend=False)
    plt.xlabel("Node ID")
    plt.ylabel("Average Delay (ms)")
    plt.title("Average Packet Delay per Node")
    plt.savefig("plot_Delay.pdf", format="pdf", bbox_inches="tight")
    plt.close()

# Main function
def main():
    log_filename = "COOJA.testlog"

    if len(sys.argv) > 1:
        log_filename = sys.argv[1]

    if not os.access(log_filename, os.R_OK):
        print(f'The input file "{log_filename}" does not exist')
        exit(-1)

    nodes = analyze_log(log_filename)
    plot_results(nodes)

if __name__ == "__main__":
    main()
