import argparse
import re
import os

# === CLI Arguments ===
parser = argparse.ArgumentParser(description="Keep only lines between minute A and B (inclusive).")
parser.add_argument("--input", "-i", required=True, help="Input .testlog file")
parser.add_argument("--output", "-o", required=True, help="Filtered output file")
parser.add_argument("--start-minute", "-s", type=int, required=True, help="Start minute (inclusive)")
parser.add_argument("--end-minute", "-e", type=int, required=True, help="End minute (inclusive)")
args = parser.parse_args()

start_tick = args.start_minute * 60_000_000
end_tick = (args.end_minute + 1) * 60_000_000  # include end minute fully

with open(args.input, 'r') as infile, open(args.output, 'w') as outfile:
    for line in infile:
        match = re.match(r'^(\d+)', line)
        if match:
            tick = int(match.group(1))
            if start_tick <= tick < end_tick:
                outfile.write(line)

os.remove(args.input)
os.rename(args.output, args.input)
print(f"Filtered log file saved as {args.input}.")