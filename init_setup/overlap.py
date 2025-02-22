'''
stores data in dictionary with instance_id as key and entry as value -- this way we can easily check for duplicates and keep only unique entries in the final file.
'''

import json
import argparse

parser = argparse.ArgumentParser()

parser.add_argument('--file1', type=str, help='path to first file')
parser.add_argument('--file2', type=str, help='path to second file')
parser.add_argument('--output', type=str, help='path to output file')

file1 = parser.parse_args().file1
file2 = parser.parse_args().file2
output_file = parser.parse_args().output

assert file1 is not None, "file1 is required, --file1"
assert file2 is not None, "file2 is required, --file2"
assert output_file is not None, "output file is required, --output"

unique_entries = {}

def process_file(filename):
    with open(filename, 'r') as f:
        for line in f:
            
            entry = json.loads(line.strip())
            unique_entries[entry["instance_id"]] = entry
        
process_file(file1)        
process_file(file2)

with open(output_file, 'w') as out:
    for entry in unique_entries.values():
        out.write(json.dumps(entry) + '\n')

print(f"merged file saved with {len(unique_entries)} unique entries.")