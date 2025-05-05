#!/usr/bin/env python3

import os
import sys
import matplotlib.pyplot as plt
import pandas as pd
from collections import defaultdict

# Class to store node statistics
class NodeStats:
    def __init__(self, node_id):
        self.node_id = node_id
        self.rpl_switches = 0
        self.sent_multicast_dio = 0
        self.sent_dao = 0

        self.packets_sent = 0
        self.packets_received = 0

# Function to process log file and extract relevant data
def analyze_log(filename):
    nodes = defaultdict(lambda: NodeStats(0))

    with open(filename, "r") as file:
        for line in file:
            fields = line.strip().split()

            try:
                node_id = int(fields[1])  # second column is node ID
            except:
                continue
            if node_id not in nodes:
                nodes[node_id] = NodeStats(node_id)

            # Detect sent multicast DIOs
            # 66541000 5 [INFO: RPL       ] Sending a multicast-DIO with rank 434
            if "multicast-DIO" in line:
                nodes[node_id].sent_multicast_dio += 1

            # Detect sent DAOs
            # 68735000 3 [INFO: RPL       ] Sending a DAO with sequence number 243, lifetime 30, prefix fd00::203:3:3:3 to fe80::205:5:5:5 , parent fe80::205:5:5:5
            if "Sending a DAO" in line:
                nodes[node_id].sent_dao += 1

            # Detect RPL parent switches
            # 2497128 2 [INFO: RPL       ] rpl_set_preferred_parent fe80::201:1:1:1 used to be NULL
            if "rpl_set_preferred_parent" in line:
                nodes[node_id].rpl_switches += 1

            # Detect sent packets
            # 60382000 1 Send to: ff1e::89:abcd Remote Port 3001, (msg=0x00000000) 4 bytes
            if "Send to:" in line:
                nodes[node_id].packets_sent += 1

            # Detect received packets
            # 60406056 2 In: [0x00000000], TTL 64, total 1
            if " In:" in line:
                nodes[node_id].packets_received += 1
    return nodes

# Function to plot results
def plot_results(nodes):

    ids = list(sorted(nodes.keys()))
    dio_values = [nodes[n].sent_multicast_dio for n in ids]
    dao_values = [nodes[n].sent_dao for n in ids]
    parent_switches = [nodes[n].rpl_switches for n in ids]

    print("Node ID\tDIOs\tDAOs\tParent switches")
    print("-------\t----\t----\t---------------")
    print(parent_switches)

    df = pd.DataFrame({"DIOs": dio_values, "DAOs": dao_values}, index=ids)
    df.plot(kind="bar", stacked=False)

    plt.xlabel("Node ID")
    plt.ylabel("# Packets")
    plt.title("Number of sent multicast DIOs and DAOs per node")
    plt.legend()
    plt.savefig("plot_DIO_DAO.pdf", format="pdf", bbox_inches="tight")
    plt.close()

    plt.bar(ids, parent_switches)
    plt.xlabel("Node ID")
    plt.ylabel("# Parent switches")
    plt.title("Number of RPL parent switches per node")
    plt.savefig("plot_parent_switches.pdf", format="pdf", bbox_inches="tight")
    plt.close()

# Main function
def main():
    log_filename = "code/analyses/COOJA.testlog"

    if len(sys.argv) > 1:
        # change from the default
        log_filename = sys.argv[1]

    if not os.access(log_filename, os.R_OK):
        print('The input file "{}" does not exist'.format(log_filename))
        exit(-1)

    nodes = analyze_log(log_filename)
    plot_results(nodes)


if __name__ == "__main__":
    main()
