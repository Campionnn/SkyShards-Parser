# SkyShards Parser
### Python script to algorithmically generate all possible recipes based on info from the wiki
## Steps
1. Download the html from the [attributes page](https://wiki.hypixel.net/Attributes) on the Hypixel Wiki. Only the HTML is needed
2. Name the download `Attributes - Hypixel SkyBlock Wiki.htm` if not already and put it in the same directory as this script
3. Run `scrape-wiki.py` and fix any mistakes such as missing icons in the wiki
4. This will generate `dist/fusion-properties.json` and any fusion info can be adjusted for wiki inaccuracies
5. Run `find-all-recipes.py` which will generate `dist/fusion-recipes.json` of all possible fusions based on the rules of fusion and wiki data
6. Run `format-fusions.py` to format the data in a way that's easier to be used
7. This will create `dist/fusion-data.json` which is used by [SkyShards](https://skyshards.com)