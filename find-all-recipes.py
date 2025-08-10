import json


with open("fusion-properties.json", "r", encoding="utf-8") as f:
    data = json.load(f)


results_length = 3
all_ids = list(data.keys())
name_map = {}
for id_, attributes in data.items():
    name = attributes.get("name", "")
    if name:
        name_map[name] = id_
rarities = ["Common", "Uncommon", "Rare", "Epic", "Legendary"]
rarity_letters = [rarity[0] for rarity in rarities]
categories = ["Forest", "Water", "Combat"]
families = set()
for attributes in data.values():
    family = attributes.get("family", None)
    if family and len(family) > 0:
        families.update(set(family))
shard_groups = {
    "Mining Shards": ["C10", "C36", "U6", "R33", "E15", "E36"]
    # "Fiery Shards": ["C30", "U33", "R56", "E14", "E15", "E18", "L28"] # Might be useful later
}


def get_next_id(current_id, count=1):
    prefix, number = current_id[0], current_id[1:]
    return f"{prefix}{int(number) + count}"


def get_next_rarity(current_rarity):
    index = rarity_letters.index(current_rarity)
    if index == len(rarity_letters) - 1:
        return None
    return rarity_letters[index + 1]


def chameleon_helper(input_, results):
    if input_ in all_ids and input_ != "L4":
        return input_
    next_rarity = get_next_rarity(input_[0])
    if not next_rarity:
        return None
    last_id = all_ids[-1]
    new_id = ''
    while new_id not in all_ids or new_id in results:
        new_id = get_next_id(f"{next_rarity}{new_id[1:] if new_id else 0}")
        if next_rarity == last_id[0] and new_id[1:] >= last_id[1:]:
            return None
        if new_id in all_ids and new_id not in results and new_id != "L4":
            return new_id
    return None


def find_chameleon_results(input_):
    results = []
    for i in range(results_length):
        result = chameleon_helper(get_next_id(input_, i+1), results)
        if result:
            results.append(result)
    return results


def get_category(input_):
    return data.get(input_, {}).get("category", None)


def get_id_result(input_):
    return name_map.get(data.get(input_, {}).get("id_result"), None)


def find_id_fusion_results(input1, input2):
    results = []
    if get_category(input1) != get_category(input2):
        result1 = get_id_result(input1)
        if result1:
            results.append(result1)
        result2 = get_id_result(input2)
        if result2:
            results.append(result2)
    else:
        if input1[0] == input2[0]:
            result2 = get_id_result(input2)
            if result2:
                if result2 != input1:
                    results.append(result2)
                else:
                    result1 = get_id_result(input1)
                    if result1:
                        results.append(result1)
        else:
            if rarity_letters.index(input1[0]) > rarity_letters.index(input2[0]):
                result1 = get_id_result(input1)
                if result1:
                    results.append(result1)
            else:
                result2 = get_id_result(input2)
                if result2:
                    results.append(result2)
    return results


def get_rarity_membership(input_, group):
    if "+" in group:
        input_index = rarity_letters.index(input_[0])
        group_index = rarity_letters.index(group[0])
        return input_index >= group_index
    else:
        return input_[0] == group[0]


def get_category_membership(input_, group):
    return data.get(input_, {}).get("category", None) == group


def get_family_membership(input_, group):
    return group in data.get(input_, {}).get("family", [])


def get_name(input_):
    return data.get(input_, {}).get("name", None)


def match_member(input_, member):
    if member == "Any":
        return True
    elif member.strip("+") in rarities:
        return get_rarity_membership(input_, member)
    elif member in categories:
        return get_category_membership(input_, member)
    elif member in families:
        return get_family_membership(input_, member)
    elif member in shard_groups:
        return input_ in shard_groups[member]
    else:
        if member.endswith(" Shard"):
            if get_name(input_) != member.replace(" Shard", ""):
                return False
        if get_name(input_) == member.replace(" Shard", ""):
            return True
        return False

def check_membership(input_, group):
    if "&" in group:
        members = group.split("&")
        return all(match_member(input_, member) for member in members)
    elif "|" in group:
        members = group.split("|")
        return any(match_member(input_, member) for member in members)
    else:
        return match_member(input_, group)


sp_fusion_map = {}
for id_, attributes in data.items():
    sp_input1 = attributes.get("input1", None)
    sp_input2 = attributes.get("input2", None)
    if sp_input1 and not sp_input2:
        sp_input2 = "Any"
    elif not sp_input1 and sp_input2:
        sp_input1 = "Any"
    sp_fusion_map[id_] = [sp_input1, sp_input2]


def find_special_fusion_results(input1, input2):
    matching_fusions = []
    for id__, inputs in sp_fusion_map.items():
        if id__ == input1 or id__ == input2:
            continue
        if ((check_membership(input1, inputs[0]) and check_membership(input2, inputs[1])) or
            (check_membership(input1, inputs[1]) and check_membership(input2, inputs[0]))):
            matching_fusions.append(id__)
    matching_fusions.sort(key=lambda x: (len(rarity_letters) - rarity_letters.index(x[0]), int(x[1:])))
    return matching_fusions[:results_length]


def test_fusion(input1_, input2_):
    if input1_ == "L4":
        results = find_chameleon_results(input2_)
        return [{"id": res, "count": 1} for res in results]
    elif input2_ == "L4":
        results = find_chameleon_results(input1_)
        return [{"id": res, "count": 1} for res in results]
    id_results = find_id_fusion_results(input1_, input2_)
    sp_results = find_special_fusion_results(input1_, input2_)
    results_ = []
    for res in id_results:
        results_.append({"id": res, "count": 1})
    for res in sp_results:
        results_.append({"id": res, "count": 2})
    return results_[:results_length]


def generate_fusion_recipes():
    fusion_recipes_ = {}
    for i in range(len(all_ids)):
        for j in range(len(all_ids)):
            input1 = all_ids[i]
            input2 = all_ids[j]
            result = test_fusion(input1, input2)
            if result:
                fusion_key = f"{input1}+{input2}"
                fusion_recipes_[fusion_key] = result
        print(f"Processed all permutations for {i+1}/{len(all_ids)} shards")
    return fusion_recipes_


fusion_data = {}
fusion_recipes = generate_fusion_recipes()
fusion_data["recipes"] = fusion_recipes
with open("fusion-recipes.json", "w", encoding="utf-8") as f:
    json.dump(fusion_data, f, indent=2, ensure_ascii=False)
