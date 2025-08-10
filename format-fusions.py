import json
from collections import defaultdict, OrderedDict
import re


prefix_order = {'C': 0, 'U': 1, 'R': 2, 'E': 3, 'L': 4}


def parse_component(component):
    match = re.match(r'([A-Z])(\d+)$', component)
    if match:
        prefix, number = match.groups()
        return prefix_order.get(prefix, 999), int(number)
    return 999, 999


with open('fusion-recipes.json', 'r') as f:
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

with open('fusion-data.json', 'w') as f:
    f.write(json_str)
