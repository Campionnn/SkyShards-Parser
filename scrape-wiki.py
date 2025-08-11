from bisect import insort
from bs4 import BeautifulSoup
from functools import cmp_to_key
import hashlib
import json
import os
import sys

output_path = "dist/fusion-properties.json"
override_path = "override-fusion-properties.json"
hashes_path = "shard-hashes.json"

github_actions = os.environ.get('GITHUB_ACTIONS')

# Parse arguments (cba to do this properly)
update_hashes = False
for arg in sys.argv[1:]:
    match arg:
        case "--update-hashes":
            update_hashes = True

# Load HTML content
with open("Attributes - Hypixel SkyBlock Wiki.htm", encoding="utf-8") as f:
    soup = BeautifulSoup(f, "html.parser")

# Define rarities
rarity_names = {
    "Common_": "Common",
    "Uncommon_": "Uncommon",
    "Rare_": "Rare",
    "Epic_": "Epic",
    "Legendary_": "Legendary"
}
rarity_letters = [rarity[0] for rarity in rarity_names.values()]

def cmp_id(a, b):
    rarity_cmp = rarity_letters.index(a[0]) - rarity_letters.index(b[0])
    return rarity_cmp or int(a[1:]) - int(b[1:])

output = {}

# Extract tables by rarity section
for section_id in rarity_names.keys():
    section = soup.find("div", id=section_id)
    if not section:
        continue

    table = section.find("table")
    if not table:
        continue

    rows = table.find_all("tr")[1:]
    for row in rows:
        cols = row.find_all("td")
        if len(cols) < 6:
            continue

        name = cols[0].get_text(strip=True)
        id_text = cols[2].get_text(strip=True)
        category = cols[3].get_text(strip=True)
        family = cols[4].get_text(strip=True).replace('None', '')
        family = [item.strip() for item in family.split(',')] if family else []
        input1 = cols[7].get_text(strip=True).replace('—', '').replace('⟦AND⟧', '&').replace('⟦OR⟧', '|')
        input2 = cols[8].get_text(strip=True).replace('—', '').replace('⟦AND⟧', '&').replace('⟦OR⟧', '|')
        id_result = cols[9].get_text(strip=True).replace('—', '')
        id_origin = cols[10].get_text(strip=True).replace('—', '').replace('"	"', '')
        id_origin = [item.strip().strip('"') for item in id_origin.split(',') if item.strip().strip('"')]

        shard_id = f"{id_text}"
        if shard_id.isdigit():
            shard_id = f"{section_id[0]}{shard_id}"
        else:
            continue

        output[shard_id] = {
            "name": name,
            "rarity": rarity_names[section_id],
            "category": category,
            "family": family,
            "input1": input1,
            "input2": input2,
            "id_result": id_result,
            "id_origin": id_origin,
        }

# Add override properties
with open(override_path, encoding="utf-8") as f:

    override_data = json.load(f)
if update_hashes:
    hashes = {}
else:
    with open(hashes_path, encoding="utf-8") as f:
        hashes = json.load(f)
for shard_id in sorted(output.keys() | override_data.keys(), key=cmp_to_key(cmp_id)):
    stored_hash = hashes.get(shard_id)
    properties = override_data.get(shard_id, {})
    if shard_id in output:
        pretty_name = f"{output[shard_id]["name"]}({shard_id})"
        hash_ = hashlib.sha256(json.dumps(output[shard_id]).encode('utf-8')).digest().hex()
        mismatch = False
        if update_hashes:
            hashes[shard_id] = hash_
        elif stored_hash != hash_:
            mismatch = True
            if github_actions:
                print("::warning file={override_path},title=Hash mismatch: {pretty_name}::expected: {hash_}")
            else:
                print(f"Hash mismatch: {pretty_name}\n"
                      f"  expected: {hash_}")
        for property_ in properties:
            if property_[0] != "_":
                output[shard_id][property_] = properties[property_]
    elif properties:
        new_entry = {
            "name": properties.get("name", shard_id),
            "rarity": properties.get("rarity", ""),
            "category": properties.get("category", ""),
            "family": properties.get("family", []),
            "input1": properties.get("input1", ""),
            "input2": properties.get("input2", ""),
            "id_result": properties.get("id_result", ""),
            "id_origin": properties.get("id_origin", []),
        }
        output_items = list(output.items())
        insort(output_items, (shard_id, new_entry), key=cmp_to_key(
            lambda a, b: cmp_id(a[0], b[0])
        ))
        output = dict(output_items)

# Make dist directory if it doesn't exist
if not os.path.exists("dist"):
    os.makedirs("dist")

# Save to JSON
with open(output_path, "w", encoding="utf-8") as f:
    json.dump(output, f, indent=2, ensure_ascii=False)
if update_hashes:
    with open(hashes_path, "w", encoding="utf-8") as f:
        json.dump(hashes, f, indent=2, ensure_ascii=False)
