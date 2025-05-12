import re

last_time = 9121270000  # Replace with your actual value

input_path = 'code/analyses/logfiles/TSCH_1_3.testlog'
output_path = 'code/analyses/logfiles/TSCH_1_3_trimmed.testlog'

with open(input_path, 'r') as infile, open(output_path, 'w') as outfile:
    for line in infile:
        match = re.match(r'^(\d+)\s+', line)
        if match:
            timestamp = int(match.group(1))
            if timestamp <= last_time:
                outfile.write(line)
        else:
            outfile.write(line)  # optionally keep non-timestamped lines
