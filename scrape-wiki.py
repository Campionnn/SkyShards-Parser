from bs4 import BeautifulSoup
import json

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

output = {}

# Extract tables by rarity section
for section_id in rarity_names.keys():
    section = soup.find("div", id=section_id)
    if not section:
        continue

    table = section.find("table")
    if not table:
        continue

    rows = table.find_all("tr")[1:]  # skip header row
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
        # id_origin = cols[10].get_text(strip=True).replace('—', '').replace('"	"', '')
        # id_origin = [item.strip().strip('"') for item in id_origin.split(',') if item.strip().strip('"')]

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
        }

# Add override properties
with open("override-fusion-properties.json", "r") as f:
    override_data = json.load(f)
for shard_id, properties in override_data.items():
    if shard_id in output:
        for property_ in properties:
            if property_[0] != "_":
                output[shard_id][property_] = properties[property_]
    else:
        new_entry = {
            "name": properties.get("name", shard_id),
            "rarity": properties.get("rarity", ""),
            "category": properties.get("category", ""),
            "family": properties.get("family", []),
            "input1": properties.get("input1", ""),
            "input2": properties.get("input2", ""),
            "id_result": properties.get("id_result", ""),
        }
        output_items = list(output.items())
        insert_index = 0
        for idx, (existing_id, _) in enumerate(output_items):
            rarity_cmp = rarity_letters.index(existing_id[0]) - rarity_letters.index(shard_id[0])
            if rarity_cmp < 0:
                insert_index = idx + 1
                continue
            elif rarity_cmp > 0:
                break
            if int(existing_id[1:]) < int(shard_id[1:]):
                insert_index = idx + 1
            else:
                break
        output_items.insert(insert_index, (shard_id, new_entry))
        output = dict(output_items)

# Save to JSON
output_path = "dist/fusion-properties.json"
with open(output_path, "w", encoding="utf-8") as f:
    json.dump(output, f, indent=2, ensure_ascii=False)
