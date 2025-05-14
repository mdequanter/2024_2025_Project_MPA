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

cooja_input = '/home/ubuntu/Documents/project2_MPA/2024_2025_Project_MPA/code/analyses/simulation_NEW.csc'
cooja_output = "code/analyses/COOJA.testlog"
filename = "code/sender-node.c"

if (os.path.exists(cooja_output)):
    os.remove(cooja_output) # remove previous Cooja output

# from 1 to 100, with steps of 10

#messageRates = [1] + list(range(1, 6, 1))
#messageRates = [60,65,70,75]
messageRates = [10]

for sendNumbers in messageRates:


    # set number of batches per run #  Nu test voor 1 batch.  zet 2 op 31 dan hebben we 30 batches
    for batch in range(50,51):

        search_text = "XXXSEND_INTERVALXXX"
        replace_text = f'(({sendNumbers} * CLOCK_SECOND))'
        print (replace_text)
        sendrate = sendNumbers   # 1 message per minute

        logfile = f"code/analyses/logfiles/TSCH_{sendrate}_{batch}.testlog"

        print (f"Processing batch {batch} with  sendrate : {sendrate}")

        # Read the file content
        with open(filename, "r") as file:
            content = file.read()

        # Replace the text
        content = content.replace(search_text, replace_text)

        # Write the updated content back to the same file
        with open(filename, "w") as file:
            file.write(content)


        # Read the file content
        with open("code/analyses/coojalogger.js", "r") as file2:
            content = file2.read()

        # Replace the text
        replaceTimout = str(int(15000000*(sendNumbers/60)))
        print (replaceTimout)
        content = content.replace('XXXtimeoutXXX', replaceTimout)

        # Write the updated content back to the same file
        with open("code/analyses/coojalogger.js", "w") as file2:
            file2.write(content)



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
                    # print (line)
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

        
        with open("code/analyses/coojalogger.js", "r") as file2:
            content = file2.read()   

        # Replace the text
        content = content.replace(replaceTimout,'XXXtimeoutXXX')

        with open("code/analyses/coojalogger.js", "w") as file2:
            file2.write(content)
    