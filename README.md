# SkyShards Parser
### Python script to algorithmically generate all possible recipes based on info from the wiki
## Steps
1. Download the html from the [attributes page](https://wiki.hypixel.net/Attributes) on the Hypixel Wiki. Only the HTML is needed
2. Run `scrape-html.py` and fix any mistakes such as missing icons in the wiki
3. This will generate `attribute_shards.json` and any fusion info can be adjusted for wiki inaccuracies
4. Run `find-all-recipes.py` which will generate `fusion-recipes.json` of all possible fusions based on the rules of fusion and wiki data
5. Run `format-fusion.py` to format the data in a way that's easier to be used
6. This will create `fusion-data.py` which is used by [SkyShards](https://skyshards.com)
