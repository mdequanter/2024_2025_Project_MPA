#!/usr/bin/env python3

import sys
import os
import re
from subprocess import Popen, PIPE, STDOUT, CalledProcessError

from collections import defaultdict

SELF_PATH = os.path.dirname(os.path.abspath(__file__))
CONTIKI_PATH = os.path.dirname(os.path.dirname(SELF_PATH))
COOJA_PATH = "/home/ubuntu/contiki-ng/tools/cooja"
cooja_input = 'simulation_TSCH.csc'
cooja_output = "code/analyses/COOJA.testlog"
filename = "code/sender-node.c"
sendrate = 1  # Example sendrate for TSCH
search_text = "XXXSEND_INTERVALXXX"
replace_text = f"(60 * CLOCK_SECOND/{sendrate})"

# Replace SEND_INTERVAL macro in code
with open(filename, "r") as file:
    content = file.read()
content = content.replace(search_text, replace_text)
with open(filename, "w") as file:
    file.write(content)

#######################################################
def run_subprocess(args, input_string):
    try:
        proc = Popen(args, stdout=PIPE, stderr=STDOUT, stdin=PIPE, shell=True, universal_newlines=True)
        (stdoutdata, stderrdata) = proc.communicate(input_string)
        return proc.returncode, stdoutdata + (stderrdata or '')
    except Exception as e:
        sys.stderr.write("Subprocess error: " + str(e))
        return -1, str(e)

#############################################################
def execute_test(cooja_file):
    try:
        os.remove(cooja_output)
    except FileNotFoundError:
        pass
    except PermissionError as ex:
        print("Cannot remove previous Cooja output:", ex)
        return False

    filename = os.path.join(SELF_PATH, cooja_file)
    args = " ".join([
        COOJA_PATH + "/gradlew --no-watch-fs --parallel --build-cache -p", COOJA_PATH,
        "run --args='--contiki=" + CONTIKI_PATH,
        "--no-gui", "--logdir=" + SELF_PATH, filename + "'"
    ])
    print(f"\n🟡 Running Cooja simulation...\nCommand: {args}")

    retcode, output = run_subprocess(args, '')
    if retcode != 0:
        print("❌ Cooja run failed.\nOutput:\n", output)
        return False

    print("🔍 Checking for COOJA.testlog...")

    is_done = False
    with open(cooja_output, "r") as f:
        for line in f:
            if "TEST OK" in line.strip():
                print("✅ TEST OK found. Log created: COOJA.testlog")
                is_done = True
                break

    if not is_done:
        print("❌ Simulation did not complete successfully (no TEST OK)")
        return False

    return True

#######################################################
def main():
    if not os.access(cooja_input, os.R_OK):
        print(f"❌ Simulation script '{cooja_input}' does not exist.")
        exit(-1)

    print(f"📁 Using simulation script: {cooja_input}")
    if not execute_test(cooja_input):
        exit(-1)

    print("\n✅ Simulation completed successfully.")

    # Restore original code
    with open(filename, "r") as file:
        content = file.read()
    content = content.replace(replace_text, search_text)
    with open(filename, "w") as file:
        file.write(content)
    print("🔄 Code restored to original placeholder.")

#######################################################
if __name__ == '__main__':
    main()
