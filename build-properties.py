from functools import cmp_to_key
from collections import Counter
from typing import Any
import hashlib
import json
import os
import sys

output_path = "dist/fusion-properties.json"
source_path = "fusion-properties.json"
shard_data_path = "shard-data.json"
hashes_path = "shard-hashes.json"

github_actions = os.environ.get('GITHUB_ACTIONS')

# Parse arguments (cba to do this properly)
update_hashes = github_actions
for arg in sys.argv[1:]:
    match arg:
        case "--update-hashes":
            update_hashes = True

# Define rarities
rarity_names = {
    "Common": "Common",
    "Uncommon": "Uncommon",
    "Rare": "Rare",
    "Epic": "Epic",
    "Legendary": "Legendary"
}
rarity_letters = [rarity[0] for rarity in rarity_names.values()]

def parse_id(id_):
    base, _, suffix = id_[1:].partition("-")
    return rarity_letters.index(id_[0]), int(base), int(suffix) if suffix else 0

def cmp_id(a, b):
    ka, kb = parse_id(a), parse_id(b)
    return (ka > kb) - (ka < kb)

# Load source data
with open(source_path, encoding="utf-8") as f:
    output: dict[str, dict[str, Any]] = json.load(f)
with open(shard_data_path, encoding="utf-8") as f:
    shard_data: dict[str, Any] = json.load(f)["shards"]
with open(hashes_path, encoding="utf-8") as f:
    hashes = json.load(f)
updated_hashes = {}
changed_shards = []

missing_property_ids = sorted(set(shard_data) - set(output), key=cmp_to_key(cmp_id))
extra_property_ids = sorted(set(output) - set(shard_data), key=cmp_to_key(cmp_id))
name_mismatches = [
    shard_id
    for shard_id in sorted(set(output) & set(shard_data), key=cmp_to_key(cmp_id))
    if output[shard_id]["name"] != shard_data[shard_id]["name"]
]
name_counts = Counter(properties["name"] for properties in output.values())
duplicate_names = sorted(name for name, count in name_counts.items() if count > 1)

validation_errors = []
if missing_property_ids:
    validation_errors.append(f"missing fusion properties for: {', '.join(missing_property_ids)}")
if extra_property_ids:
    validation_errors.append(f"fusion properties without shard data: {', '.join(extra_property_ids)}")
if name_mismatches:
    validation_errors.append(
        "fusion property names do not match shard data: "
        + ", ".join(
            f"{shard_id} ({output[shard_id]['name']} != {shard_data[shard_id]['name']})"
            for shard_id in name_mismatches
        )
    )
if duplicate_names:
    validation_errors.append(f"duplicate fusion property names: {', '.join(duplicate_names)}")
if validation_errors:
    raise ValueError("\n".join(validation_errors))

# Calculate id_origin based on id_result relationships
for shard_id, properties in output.items():
    id_origin_ids = []
    # Find all shards that have this shard as their id_result
    for other_id, other_properties in output.items():
        if other_properties.get("id_result") == properties.get("name"):
            id_origin_ids.append(other_id)
    properties["id_origin"] = [
        output[other_id]["name"]
        for other_id in sorted(id_origin_ids, key=cmp_to_key(cmp_id))
    ]

# Process all shards for hashing and change detection
for shard_id in sorted(output.keys(), key=cmp_to_key(cmp_id)):
    stored_hash = hashes.get(shard_id)
    pretty_name = f"{output[shard_id]['name']}({shard_id})"
    hash_ = hashlib.sha256(json.dumps(output[shard_id]).encode('utf-8')).hexdigest()  # type: ignore[arg-type]
    updated_hashes[shard_id] = hash_
    if stored_hash != hash_:
        if github_actions:
            changed_shards.append(pretty_name)
        elif not update_hashes:
            print(f"Hash mismatch: {pretty_name}\n"
                  f"  expected: {hash_}")

# Make dist directory if it doesn't exist
if not os.path.exists("dist"):
    os.makedirs("dist")

# Save to JSON
with open(output_path, "w", encoding="utf-8") as f:
    json.dump(output, f, indent=2, ensure_ascii=False)
if update_hashes:
    with open(hashes_path, "w", encoding="utf-8") as f:
        json.dump(updated_hashes, f, indent=2, ensure_ascii=False)
if github_actions:
    with open("changed-shards.txt", "w", encoding="utf-8") as f:
        for name in changed_shards:
            f.write(f"{name}\n")
