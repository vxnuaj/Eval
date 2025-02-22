import json

input_file = '../input.jsonl'
output_file = '../input_filtered.jsonl'
query_ids_file = '../query_ids.json'

with open(input_file, 'r') as infile:
    lines = infile.readlines()

with open(query_ids_file, 'r') as f:
    query_ids = json.load(f)

filtered_lines = []

for line in lines:
    data = json.loads(line)
    if data.get("instance_id") in query_ids:
        filtered_lines.append(data)

for i, data in enumerate(filtered_lines):
    data["instance_id"] = i  

with open(output_file, 'w') as outfile:
    for data in filtered_lines:
        outfile.write(json.dumps(data) + '\n')

print(f"Filtered data written to {output_file}")
