import json
from collections import defaultdict, OrderedDict
import re
import hashlib
import subprocess


prefix_order = {'C': 0, 'U': 1, 'R': 2, 'E': 3, 'L': 4}


def parse_component(component):
    match = re.match(r'([A-Z])(\d+)$', component)
    if match:
        prefix, number = match.groups()
        return prefix_order.get(prefix, 999), int(number)
    return 999, 999


with open('dist/fusion-recipes.json', 'r') as f:
    data = json.load(f)

# transform the recipes
new_recipes = defaultdict(lambda: defaultdict(list))
for input_combo, results in data['recipes'].items():
    inputs = input_combo.split('+')
    for result in results:
        result_id = result['id']
        count = str(result['count'])
        new_recipes[result_id][count].append(inputs)

# sort
final_recipes = OrderedDict()
for result_id in sorted(new_recipes.keys(), key=parse_component):
    count_dict = new_recipes[result_id]
    count_ordered = OrderedDict()
    for count, input_lists in sorted(count_dict.items(), key=lambda item: int(item[0])):
        input_lists.sort(key=lambda pair: (parse_component(pair[0]), parse_component(pair[1])))
        count_ordered[count] = input_lists
    final_recipes[result_id] = count_ordered

data['recipes'] = final_recipes


with open('shard-data.json', 'r') as f:
    shards = json.load(f)

# sort shards
sorted_shards = OrderedDict(
    sorted(shards['shards'].items(), key=lambda item: parse_component(item[0]))
)
data['shards'] = sorted_shards


def format_dict_inline(d):
    items = [f'"{k}": {json.dumps(v)}' for k, v in d.items()]
    return '{ ' + ', '.join(items) + ' }'


# custom JSON encoder
class JsonEncoder(json.JSONEncoder):
    def encode(self, obj):
        shards_ = obj.get("shards", {})
        compact_shards = {k: format_dict_inline(v) for k, v in shards_.items()}

        obj_copy = dict(obj)
        del obj_copy["shards"]
        base_json = json.dumps(obj_copy, indent=2)

        base_json = base_json.rstrip()
        if base_json.endswith("}"):
            base_json = base_json[:-1].rstrip()

        if base_json.strip() != "{":
            base_json += ",\n"
        else:
            base_json += "\n"

        shard_lines = [f'    "{k}": {v}' for k, v in compact_shards.items()]
        shards_block = '  "shards" : {\n' + ',\n'.join(shard_lines) + '\n  }'

        json_result = base_json + shards_block + "\n}"

        json_result = re.sub(
            r'\[\s*"([^"]+)",\s*"([^"]+)"\s*\]',
            r'["\1", "\2"]',
            json_result
        )

        return json_result


json_str = json.dumps(data, indent=2, cls=JsonEncoder)

with open('dist/fusion-data.json', 'w') as f:
    f.write(json_str)

with open('dist/fusion-data.json', 'rb') as f:
    fusion_data_bytes = f.read()
    fusion_data_hash = hashlib.sha256(fusion_data_bytes).hexdigest()

shard_hashes_path = 'shard-hashes.json'

try:
    result = subprocess.run(['git', 'show', 'HEAD:shard-hashes.json'], capture_output=True, text=True, check=True)
    committed_hashes = json.loads(result.stdout)
    old_fusion_data_hash = committed_hashes.get('fusion-data')
except (subprocess.CalledProcessError, json.JSONDecodeError, FileNotFoundError):
    old_fusion_data_hash = None

try:
    with open(shard_hashes_path, 'r') as f:
        shard_hashes = json.load(f)
except FileNotFoundError:
    shard_hashes = {}

if old_fusion_data_hash != fusion_data_hash:
    with open('changed-shards.txt', 'a') as f:
        f.write(f"fusion-data hash changed from {old_fusion_data_hash} to {fusion_data_hash}\n")

ordered_hashes = OrderedDict()
ordered_hashes['fusion-data'] = fusion_data_hash

for key, value in shard_hashes.items():
    if key != 'fusion-data':
        ordered_hashes[key] = value

with open(shard_hashes_path, 'w') as f:
    json.dump(ordered_hashes, f, indent=2)
