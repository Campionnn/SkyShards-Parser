import json
import re

input_filename = 'shard_weighting.json'

with open(input_filename, 'r') as f:
    data_str = f.read()

# Parse JSON
data = json.loads(data_str)

# Extract weights with Infinity (null) replaced by 0
weights = {}
for key, value in data.items():
    weight = value.get("weight", 0)
    if weight is None:
        weight = 0
    weights[key] = weight * 60

# Custom sort order based on prefix
prefix_order = {'C': 0, 'U': 1, 'R': 2, 'E': 3, 'L': 4}


def sort_key(k):
    match = re.match(r'^([A-Z]+)(\d+)$', k)
    if not match:
        return 99, 9999  # fallback
    prefix, num = match.groups()
    return prefix_order.get(prefix, 99), int(num)


# Sort weights
sorted_weights = {k: weights[k] for k in sorted(weights, key=sort_key)}

# Write the rates.json
output_filename = 'rates.json'
with open(output_filename, 'w') as f:
    json.dump(sorted_weights, f, indent=2)
