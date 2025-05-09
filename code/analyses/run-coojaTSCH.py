#!/usr/bin/env python3

import sys
import os
from subprocess import Popen, PIPE, STDOUT, CalledProcessError
from datetime import datetime


saveLogs = True  # Set to True to save the logs, False to delete them

timestampbatch = datetime.now().strftime('%Y%m%d%H%M%S')

# get the path of this example
SELF_PATH = os.path.dirname(os.path.abspath(__file__))
# move three levels up
CONTIKI_PATH = os.path.dirname(os.path.dirname(SELF_PATH))

# COOJA_PATH = os.path.normpath(os.path.join(CONTIKI_PATH, "tools", "cooja"))
COOJA_PATH = "/home/ubuntu/contiki-ng/tools/cooja"

cooja_input = '/home/ubuntu/Documents/project2_MPA/2024_2025_Project_MPA/code/analyses/simulation_TSCH_28.csc'
cooja_output = "code/analyses/COOJA.testlog"
csv_output = f"code/analyses/COOJA_{timestampbatch}.csv"
filename = "code/sender-node.c"


# from 1 to 100, with steps of 10

#messageRates = [1] + list(range(1, 6, 1))
messageRates = [1]
for sendPerMinute in messageRates:


    # set number of batches per run #  Nu test voor 1 batch.  zet 2 op 31 dan hebben we 30 batches
    for batch in range(1, 5):

        search_text = "XXXSEND_INTERVALXXX"
        replace_text = f"(60 * CLOCK_SECOND/{sendPerMinute})"
        print (replace_text)
        sendrate = sendPerMinute   # 1 message per minute

        logfile = f"code/analyses/logfiles/TSCH_{sendrate}_{batch}.testlog"

        # Read the file content
        with open(filename, "r") as file:
            content = file.read()

        # Replace the text
        content = content.replace(search_text, replace_text)

        # Write the updated content back to the same file
        with open(filename, "w") as file:
            file.write(content)



        #######################################################
        # Run a child process and get its output

        def run_subprocess(args, input_string):
            retcode = -1
            stdoutdata = ''
            try:
                proc = Popen(args, stdout=PIPE, stderr=STDOUT, stdin=PIPE, shell=True, universal_newlines=True)
                (stdoutdata, stderrdata) = proc.communicate(input_string)
                if not stdoutdata:
                    stdoutdata = '\n'
                if stderrdata:
                    stdoutdata += stderrdata + '\n'
                retcode = proc.returncode
            except OSError as e:
                sys.stderr.write("run_subprocess OSError:" + str(e))
            except CalledProcessError as e:
                sys.stderr.write("run_subprocess CalledProcessError:" + str(e))
                retcode = e.returncode
            except Exception as e:
                sys.stderr.write("run_subprocess exception:" + str(e))
            finally:
                return (retcode, stdoutdata)

        #############################################################
        # Run a single instance of Cooja on a given simulation script

        def execute_test(cooja_file):
            # cleanup
            try:
                os.remove(cooja_output)
            except FileNotFoundError as ex:
                pass
            except PermissionError as ex:
                print("Cannot remove previous Cooja output:", ex)
                return False

            filename = os.path.join(SELF_PATH, cooja_file)
            args = " ".join([COOJA_PATH + "/gradlew --no-watch-fs --parallel --build-cache -p", COOJA_PATH, "run --args='--contiki=" + CONTIKI_PATH, "--no-gui", "--logdir=" + SELF_PATH, filename + "'"])
            sys.stdout.write("  Running Cooja, args={}\n".format(args))

            (retcode, output) = run_subprocess(args, '')
            if retcode != 0:
                sys.stderr.write("Failed, retcode=" + str(retcode) + ", output:")
                sys.stderr.write(output)
                return False

            sys.stdout.write("  Checking for output...")

            is_done = False
            with open(cooja_output, "r") as f:
                for line in f.readlines():
                    line = line.strip()
                    if line == "TEST OK":
                        sys.stdout.write(" done.\n")
                        is_done = True
                        continue

            if not is_done:
                sys.stdout.write("  test failed.\n")
                return False

            sys.stdout.write(" test done\n")
            return True

        #######################################################
        # Run the application

        def main():
            input_file = cooja_input
            if len(sys.argv) > 1:
                # change from the default
                input_file = sys.argv[1]

            if not os.access(input_file, os.R_OK):
                print('Simulation script "{}" does not exist'.format(input_file))
                exit(-1)

            print('Using simulation script "{}"'.format(input_file))
            if not execute_test(input_file):
                exit(-1)

        #######################################################

        if __name__ == '__main__':
            main()


        ########################################################


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

        # Extra: "not for us" warnings per node
        not_for_us_counts = defaultdict(int)

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

        print("\nSender Node | Avg Delay (s)  | Sent | Received | Success % | Throughput (Bps) | Not-for-us | Avg Hops")
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

            all_senders = sorted(set(sent_counts.keys()) and set(recv_counts.keys()) )
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
                        'batch': batch,
                        'timestamp':timestampbatch,
                        'logfile': logfile,
                        'sendrate': sendrate,
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

        if (saveLogs == True):
            os.rename(cooja_output, logfile)
        else:
            os.remove(cooja_output)
        # Read the file content
        with open(filename, "r") as file:
            content = file.read()   

        # Replace the text
        content = content.replace(replace_text,search_text)

        # Write the updated content back to the same file
        with open(filename, "w") as file:
            file.write(content)


