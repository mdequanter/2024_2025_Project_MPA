#!/usr/bin/env python3

import sys
import os
import re
import csv
from subprocess import Popen, PIPE, STDOUT, CalledProcessError
from datetime import datetime
from collections import defaultdict

saveLogs = False  # Set to True to save the logs, False to delete them
saveCsv = True   # Set to True to save CSV results, False to skip writing CSV

timestampbatch = datetime.now().strftime('%Y%m%d%H%M%S')

SELF_PATH = os.path.dirname(os.path.abspath(__file__))
CONTIKI_PATH = os.path.dirname(os.path.dirname(SELF_PATH))
COOJA_PATH = "/home/ubuntu/contiki-ng/tools/cooja"

cooja_input = '/home/ubuntu/Documents/project2_MPA/2024_2025_Project_MPA/code/analyses/simulation_NEW.csc'
cooja_output = "code/analyses/COOJA.testlog"
filename = "code/sender-node.c"

csv_output = "code/analyses/tsch_summary_means.csv"
sender_nodes = [str(n) for n in [10, 11, 19, 2, 20, 21, 22, 23, 24, 25, 26, 27, 28, 3, 4, 5, 6, 7, 8, 9]]

if saveCsv:
    if not os.path.exists(os.path.dirname(csv_output)):
        os.makedirs(os.path.dirname(csv_output))

    if not os.path.exists(csv_output):
        with open(csv_output, mode='w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=[
                "File", "End-to-End latency(ms)", "Sent", "Confirmed", "Received", "Throughput %", "Sendrate (Bps)"
            ])
            writer.writeheader()

if os.path.exists(cooja_output):
    os.remove(cooja_output)

messageRates = [20,15,10,8,5,1]

for sendNumbers in messageRates:
    for batch in range(6,30):

        search_text = "XXXSEND_INTERVALXXX"
        replace_text = f'(({sendNumbers} * CLOCK_SECOND))'
        sendrate = sendNumbers

        logfile = f"code/analyses/logfiles/TSCH_{sendrate}_{batch}.testlog"
        print(f"Starting batch {batch} with sendrate {sendrate}...")


        with open(filename, "r") as file:
            content = file.read().replace(search_text, replace_text)
        with open(filename, "w") as file:
            file.write(content)

        with open("code/analyses/coojalogger.js", "r") as file:
            content = file.read()
        replaceTimout = str(int(150000000 * (sendNumbers / 60)))
        with open("code/analyses/coojalogger.js", "w") as file:
            file.write(content.replace('XXXtimeoutXXX', replaceTimout))

        def run_subprocess(args, input_string):
            try:
                proc = Popen(args, stdout=PIPE, stderr=STDOUT, stdin=PIPE, shell=True, universal_newlines=True)
                stdoutdata, stderrdata = proc.communicate(input_string)
                return proc.returncode, stdoutdata + (stderrdata or '')
            except Exception as e:
                return -1, str(e)

        def execute_test(cooja_file):
            try:
                os.remove(cooja_output)
            except FileNotFoundError:
                pass
            filename = os.path.join(SELF_PATH, cooja_file)
            args = f"{COOJA_PATH}/gradlew --no-watch-fs --parallel --build-cache -p {COOJA_PATH} run --args='--contiki={CONTIKI_PATH} --no-gui --logdir={SELF_PATH} {filename}'"
            print(f"  Running Cooja, args={args}")
            retcode, output = run_subprocess(args, '')
            if retcode != 0:
                print("Failed:", output)
                return False
            with open(cooja_output, "r") as f:
                return any("TEST OK" in line for line in f)

        if __name__ == '__main__':
            if not execute_test(cooja_input):
                exit(-1)


        # Revert changes
        with open(filename, "r") as file:
            content = file.read().replace(replace_text, search_text)
        with open(filename, "w") as file:
            file.write(content)

        with open("code/analyses/coojalogger.js", "r") as file:
            content = file.read().replace(replaceTimout, 'XXXtimeoutXXX')
        with open("code/analyses/coojalogger.js", "w") as file:
            file.write(content)

        if saveCsv == True:

            print("=== Extracting results ===")

            # === Extract results and append to CSV ===
            try:
                with open(cooja_output, 'r') as file:
                    lines = list(file)
            except:
                continue

            sent_messages = {}
            sender_delays = defaultdict(list)
            sent_counts = defaultdict(int)
            confirmed_sent_counts = defaultdict(int)
            recv_counts = defaultdict(int)
            recv_bytes = defaultdict(int)
            first_send_time = defaultdict(lambda: float('inf'))
            last_recv_time = defaultdict(lambda: 0)

            print (f"{cooja_output} loaded successfully")

            for i, line in enumerate(lines):
                send_match = re.match(r'^(\d+)\s+(\d+)\s+Sending message: \'(.+?)\' to fd00::210:10:10:10', line)
                if send_match:
                    time, sender_node, message = int(send_match.group(1)), send_match.group(2), send_match.group(3).strip()
                    if sender_node in sender_nodes:
                        sent_counts[sender_node] += 1
                        sent_messages[message] = (time, sender_node)
                        first_send_time[sender_node] = min(first_send_time[sender_node], time)
                        for followup in lines[i+1:i+11]:
                            tsch_match = re.match(r'^\d+\s+' + sender_node + r'\s+\[INFO: TSCH\s+\] send packet to .*', followup)
                            if tsch_match:
                                confirmed_sent_counts[sender_node] += 1
                                break

                recv_match = re.match(r'^(\d+)\s+16\s+Data received from .*? in \d+ hops with datalength \d+: \'(.+?)\'', line)
                if recv_match:
                    time, message = int(recv_match.group(1)), recv_match.group(2).strip()
                    if message in sent_messages:
                        send_time, sender_node = sent_messages[message]
                        if sender_node in sender_nodes:
                            delay = time - send_time
                            sender_delays[sender_node].append(delay)
                            recv_counts[sender_node] += 1
                            recv_bytes[sender_node] += len(message)
                            last_recv_time[sender_node] = max(last_recv_time[sender_node], time)

            total_sent = total_confirmed = total_received = total_delay = total_throughput = 0
            num_senders = 0

            for sender in sender_nodes:
                sent = sent_counts[sender]
                confirmed = confirmed_sent_counts[sender]
                received = recv_counts[sender]

                if confirmed > 0 and received > 0:
                    avg_delay = sum(sender_delays[sender]) / (received * 1000)
                    time_span = (last_recv_time[sender] - first_send_time[sender]) / 1000
                    throughput = (recv_bytes[sender] / (time_span / 1000)) if time_span > 0 else 0
                    total_sent += sent
                    total_confirmed += confirmed
                    total_received += received
                    total_delay += avg_delay
                    total_throughput += throughput
                    num_senders += 1

            if num_senders > 0 and total_confirmed > 0:
                with open(csv_output, mode='a', newline='') as csvfile:
                    writer = csv.DictWriter(csvfile, fieldnames=[
                        "File", "End-to-End latency(ms)", "Sent", "Confirmed", "Received", "Throughput %", "Sendrate (Bps)"
                    ])
                    print(f"Writing to {csv_output}")
                    writer.writerow({
                        "File": os.path.basename(logfile),
                        "End-to-End latency(ms)": round(total_delay / num_senders, 2),
                        "Sent": total_sent // num_senders,
                        "Confirmed": total_confirmed // num_senders,
                        "Received": total_received // num_senders,
                        "Throughput %": round((total_received / total_confirmed) * 100, 2),
                        "Sendrate (Bps)": round(total_throughput / num_senders, 2)
                    })


        if saveLogs == True:
            os.rename(cooja_output, logfile)
        #else:
            #os.remove(cooja_output)
