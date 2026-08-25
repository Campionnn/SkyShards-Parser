"""Scrape the official attribute fusion spec from the Hypixel SkyBlock wiki.

https://hypixelskyblock.minecraft.wiki/w/User:Wiki_Editor_33/AttributeFusion

Writes fusion-properties.json. Overrides belong in
override-fusion-properties.json, which build-properties.py merges on top.
"""
import argparse
import json
import re
import sys
import urllib.request

WIKI_URL = "https://hypixelskyblock.minecraft.wiki/w/User:Wiki_Editor_33/AttributeFusion?action=raw"
OUTPUT_PATH = "fusion-properties.json"
SECTION_MARKER = "==Full Info table"

(COL_SHARD, COL_RARITY, COL_ID, COL_ATTRIBUTE, COL_CATEGORY, COL_FAMILY,
 COL_IMMUNITIES, COL_INPUT1, COL_INPUT2, COL_ID_RESULT, COL_ID_ORIGIN,
 COL_CHAM_RESULT, COL_CHAM_ORIGIN, COL_SYNTHESIZED, COL_GENERIC_TARGET,
 COL_CHAMELEON, COL_CHAM_INFO, COL_RECIPE_TYPE, COL_INTERNAL_ID,
 COL_ATTRIBUTE_RAW) = range(20)
COLUMN_COUNT = 20

TABBER_MARKER = re.compile(r"^\|-\|\w+=")
SHARD_SUFFIX = " Shard"
WIKI_PREFIX = "_wiki_"


def fetch_wikitext(from_file=None):
    if from_file:
        with open(from_file, encoding="utf-8") as f:
            return f.read()
    request = urllib.request.Request(WIKI_URL, headers={"User-Agent": "SkyShards-Parser"})
    with urllib.request.urlopen(request) as response:
        return response.read().decode("utf-8")


def split_rows(wikitext):
    lines = wikitext.splitlines()
    try:
        start = next(i for i, line in enumerate(lines) if line.startswith(SECTION_MARKER))
    except StopIteration:
        raise ValueError(f"could not find the '{SECTION_MARKER}' section in the wiki page")

    rows = []
    cells = None

    def flush():
        nonlocal cells
        if cells:
            rows.append(cells)
        cells = None

    for line in lines[start + 1:]:
        stripped = line.strip()
        if line.startswith("=="):
            break
        if stripped == "|}" or TABBER_MARKER.match(line):
            flush()
        elif stripped == "|-":
            flush()
            cells = []
        elif cells is not None and line.startswith("|"):
            cells.append(line[1:])
    flush()

    shard_rows = []
    for cells in rows:
        if not cells or "Shard}}" not in cells[COL_SHARD]:
            continue
        if len(cells) != COLUMN_COUNT:
            raise ValueError(
                f"expected {COLUMN_COUNT} columns, got {len(cells)} in row: {cells[COL_SHARD]}"
            )
        shard_rows.append(cells)
    return shard_rows


def plain(cell):
    cell = re.sub(r"\{\{ID\|\s*([^}|]+?)\s*\}\}", r"\1", cell)
    cell = re.sub(r"\{\{[Cc]olor\|[^|]+\|([^}]*)\}\}", r"\1", cell)
    cell = re.sub(r"\{\{[Rr]arity\|([^}]*)\}\}", r"\1", cell)
    cell = cell.replace("'''+'''", "+")
    return cell.strip()


def shard_name(cell):
    match = re.search(r"\{\{ID\|\s*([^}|]+?)\s*\}\}", cell)
    return match.group(1)[: -len(" Shard")].strip() if match else None


def shard_names(cell):
    return [name[: -len(" Shard")].strip() for name in re.findall(r"\{\{ID\|\s*([^}|]+?)\s*\}\}", cell)]


def parse_recipe(cell):
    text = plain(cell.replace("<br>", " "))
    text = re.sub(r"\s+", " ", text).strip()
    if not text:
        return ""
    parts = re.split(r" (AND|OR) ", text)
    expression = parts[0].strip()
    for operator, operand in zip(parts[1::2], parts[2::2]):
        expression += ("&" if operator == "AND" else "|") + operand.strip()
    return expression


def parse_family(cell):
    text = plain(cell)
    if not text:
        return []
    return [part.strip().replace("_", " ").title() for part in text.split(" and ") if part.strip()]


def internal_id(cell):
    match = re.match(r"[A-Z0-9_]+", plain(cell))
    if match is None:
        raise ValueError(f"could not read an internal shard id from {cell!r}")
    return match.group(0)


def build_alias_map(properties):
    aliases = {}
    for shard in properties.values():
        alias = shard[WIKI_PREFIX + "internal_id"].replace("_", " ")
        aliases[alias.casefold()] = shard["name"]
    return aliases


def resolve_recipe_names(expression, names, aliases):
    resolved = []
    for token in re.split(r"([&|])", expression):
        if token.endswith(SHARD_SUFFIX):
            name = token[: -len(SHARD_SUFFIX)]
            if name not in names:
                canonical = aliases.get(name.casefold())
                if canonical is None:
                    raise ValueError(f"recipe references unknown shard {name!r}")
                token = canonical + SHARD_SUFFIX
        resolved.append(token)
    return "".join(resolved)


def parse_row(cells):
    shard_id = plain(cells[COL_RARITY])[0].upper() + cells[COL_ID].strip()
    return shard_id, {
        "name": shard_name(cells[COL_SHARD]),
        "rarity": plain(cells[COL_RARITY]),
        "category": plain(cells[COL_CATEGORY]).title(),
        "family": parse_family(cells[COL_FAMILY]),
        "input1": parse_recipe(cells[COL_INPUT1]),
        "input2": parse_recipe(cells[COL_INPUT2]),
        "synthesized": "TRUE" in cells[COL_SYNTHESIZED],
        "chameleon": "yes" in cells[COL_CHAMELEON],
        "recipe_type": "GENERIC_PLUS" if "Generic Plus" in cells[COL_RECIPE_TYPE] else None,

        f"{WIKI_PREFIX}internal_id": internal_id(cells[COL_INTERNAL_ID]),
        f"{WIKI_PREFIX}id_result": shard_name(cells[COL_ID_RESULT]),
        f"{WIKI_PREFIX}id_origin": shard_names(cells[COL_ID_ORIGIN]),
        f"{WIKI_PREFIX}chameleon_result": shard_names(cells[COL_CHAM_RESULT]),
        f"{WIKI_PREFIX}chameleon_origin": shard_names(cells[COL_CHAM_ORIGIN]),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--from-file", help="parse a saved copy of the raw wikitext instead of fetching")
    parser.add_argument("--output", default=OUTPUT_PATH)
    args = parser.parse_args()

    wikitext = fetch_wikitext(args.from_file)
    rows = split_rows(wikitext)

    properties = {}
    for cells in rows:
        shard_id, shard = parse_row(cells)
        if shard_id in properties:
            raise ValueError(f"duplicate shard id {shard_id} ({shard['name']})")
        properties[shard_id] = shard

    names = {shard["name"] for shard in properties.values()}
    aliases = build_alias_map(properties)
    for shard_id, shard in properties.items():
        for field in ("input1", "input2"):
            try:
                shard[field] = resolve_recipe_names(shard[field], names, aliases)
            except ValueError as error:
                raise ValueError(f"{shard_id} ({shard['name']}): {error}") from error

    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(properties, f, indent=2, ensure_ascii=False)
    print(f"Scraped {len(properties)} shards to {args.output}")


if __name__ == "__main__":
    sys.exit(main())
