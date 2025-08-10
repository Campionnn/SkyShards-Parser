from bs4 import BeautifulSoup
import json

# Load HTML content
with open("Attributes - Hypixel SkyBlock Wiki.htm", encoding="utf-8") as f:
    soup = BeautifulSoup(f, "html.parser")

# Define rarities
rarity_sections = ["Common_", "Uncommon_", "Rare_", "Epic_", "Legendary_"]
rarity_names = {
    "Common_": "Common",
    "Uncommon_": "Uncommon",
    "Rare_": "Rare",
    "Epic_": "Epic",
    "Legendary_": "Legendary"
}

output = {}

# Extract tables by rarity section
for section_id in rarity_sections:
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
        }

# Add override properties
with open("override-fusion-properties.json", "r") as f:
    override_data = json.load(f)
for shard_id, properties in override_data.items():
    for property_ in properties:
        if property_ != "_name":
            output[shard_id][property_] = properties[property_]

# Save to JSON
output_path = "fusion-properties.json"
with open(output_path, "w", encoding="utf-8") as f:
    json.dump(output, f, indent=2, ensure_ascii=False)
